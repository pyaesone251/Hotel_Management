from odoo import models, fields


class PublisherWarrantyContract(models.AbstractModel):
    _inherit = "publisher_warranty.contract"

    def update_notification(self, cron_mode):
        # this line is needed because odoo will send different cron mode
        if isinstance(cron_mode, bool) or cron_mode is None:
            # Find model ID for 'publisher_warranty.contract'
            model = self.env["ir.model"].search(
                [("model", "=", "publisher_warranty.contract")], limit=1
            )
            if not model:
                return True
            # Find cron for this model
            cron = self.env["ir.cron"].search([("model_id", "=", model.id)], limit=1)
            # If cron not found, create a new cron
            if not cron:
                cron = self.env["ir.cron"].create(
                    {
                        "name": "Publisher Warranty Contract Auto Update",
                        "model_id": model.id,
                        "state": "code",
                        "code": "model.update_notification(None)",
                        "user_id": self.env.uid,
                        "interval_number": 1,
                        "interval_type": "months",
                        "priority": 5,
                        "active": False,
                    }
                )

            # Create log in ir_cron_trigger
            self.env["ir.cron.trigger"].create(
                {"cron_id": cron.id, "call_at": fields.Datetime.now()}
            )
        return True
