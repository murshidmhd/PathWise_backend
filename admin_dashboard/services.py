class ApprovalService:

    @staticmethod
    def approve(profile):
        if profile.approval_status == "approved":
            raise ValueError("Already approved")

        profile.approval_status = "approved"
        profile.rejection_reason = None
        profile.save()

        return profile


    @staticmethod
    def reject(profile, reason):
        # if not reason:
        #     raise ValueError("Rejection reason is required")

        profile.approval_status = "rejected"
        profile.rejection_reason = reason
        profile.save()

        return profile