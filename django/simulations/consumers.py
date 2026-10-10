import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.conf import settings
from .models import SimulationSession, SimulationMessage, PostActionReport
import google.generativeai as genai

logger = logging.getLogger(__name__)

class SimulationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.user = self.scope["user"]
        
        if self.user.is_anonymous:
            await self.close(code=4001)
            return
            
        # Verify session exists and belongs to user
        self.session = await self.get_session(self.session_id, self.user)
        if not self.session:
            await self.close(code=4004)
            return
            
        self.room_group_name = f'simulation_{self.session_id}'
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        
        # Initialize Gemini API
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-1.5-pro')

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            action = data.get('action')
            
            if action == 'user_message':
                await self.handle_user_message(data.get('text'))
            elif action == 'coach_hint':
                await self.handle_coach_hint()
            elif action == 'complete_session':
                await self.handle_complete_session()
                
        except Exception as e:
            logger.error(f"Error in receive: {str(e)}")
            await self.send_error(str(e))

    async def handle_user_message(self, text):
        if not text:
            return
            
        name = self.user.get_full_name()
        if not name:
            name = self.user.email
            
        # Save user message
        await self.save_message('USER', name, text)
        
        # Echo back to client
        await self.send_json({
            'type': 'message',
            'role': 'USER',
            'name': name,
            'text': text
        })
        
        # Determine orchestrator logic
        await self.orchestrator_turn(text)
        
    async def orchestrator_turn(self, last_user_message):
        # 1. Pick next agent
        scenario = await self.get_scenario()
        agents = scenario.agent_configs
        if not agents or not isinstance(agents, list):
            return
            
        # For simplicity MVP, pick the first agent (in a real app, logic would alternate based on context)
        agent = agents[0]
        
        # 2. Generate response using Gemini
        history = await self.get_chat_history()
        prompt = f"You are {agent.get('name', 'Agent')}. {agent.get('persona', '')}\n\nScenario context: {scenario.description}\n\nChat history:\n{history}\n\nRespond as {agent.get('name', 'Agent')}."
        
        try:
            response = self.model.generate_content(prompt)
            agent_text = response.text
            
            # Save and send
            await self.save_message('AGENT', agent.get('name', 'Agent'), agent_text)
            await self.send_json({
                'type': 'message',
                'role': 'AGENT',
                'name': agent.get('name', 'Agent'),
                'text': agent_text,
                'sentiment': 50 # Default middle sentiment for now
            })
            
        except Exception as e:
            logger.error(f"Gemini error: {e}")
            await self.send_error("AI is currently unavailable.")

    async def handle_coach_hint(self):
        history = await self.get_chat_history()
        scenario = await self.get_scenario()
        prompt = f"You are an expert career coach observing this interaction for a {scenario.title} scenario:\n{history}\nProvide a short, actionable hint for the user on what to say next."
        
        try:
            response = self.model.generate_content(prompt)
            await self.send_json({
                'type': 'coach_hint',
                'text': response.text
            })
        except Exception as e:
            await self.send_error("Coach is unavailable.")
            
    async def handle_complete_session(self):
        # Update session status
        await self.update_session_status('COMPLETED')
        
        # Evaluate session and generate PAR
        history = await self.get_chat_history()
        prompt = f"Review this chat transcript and provide a structured JSON evaluation. Transcript:\n{history}\n\nFormat your response as valid JSON with these keys: score_negotiation (0-100), score_professionalism (0-100), score_clarity (0-100), score_overall (0-100), and feedback_text (markdown string)."
        
        try:
            response = self.model.generate_content(prompt)
            # Try to parse JSON from response
            import re
            json_match = re.search(r'```json\n(.*?)\n```', response.text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(1))
            else:
                result = json.loads(response.text)
                
            report = await self.create_par(result)
            
            await self.send_json({
                'type': 'session_completed',
                'report_id': report.id
            })
            
        except Exception as e:
            logger.error(f"Error generating PAR: {e}")
            await self.send_error("Failed to generate report.")

    async def send_json(self, data):
        await self.send(text_data=json.dumps(data))
        
    async def send_error(self, message):
        await self.send_json({'error': message})

    @database_sync_to_async
    def get_session(self, session_id, user):
        try:
            return SimulationSession.objects.select_related('scenario').get(id=session_id, student=user)
        except SimulationSession.DoesNotExist:
            return None
            
    @database_sync_to_async
    def get_scenario(self):
        return self.session.scenario
        
    @database_sync_to_async
    def update_session_status(self, status):
        self.session.status = status
        self.session.save(update_fields=['status'])

    @database_sync_to_async
    def save_message(self, role, name, text):
        return SimulationMessage.objects.create(
            session=self.session,
            sender_role=role,
            sender_name=name,
            text=text
        )
        
    @database_sync_to_async
    def get_chat_history(self):
        messages = SimulationMessage.objects.filter(session=self.session).order_by('timestamp')
        return "\n".join([f"{msg.sender_name}: {msg.text}" for msg in messages])
        
    @database_sync_to_async
    def create_par(self, data):
        return PostActionReport.objects.create(
            session=self.session,
            score_negotiation=data.get('score_negotiation', 0),
            score_professionalism=data.get('score_professionalism', 0),
            score_clarity=data.get('score_clarity', 0),
            score_overall=data.get('score_overall', 0),
            feedback_text=data.get('feedback_text', '')
        )
