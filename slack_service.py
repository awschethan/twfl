import requests
import logging

logger = logging.getLogger(__name__)

class SlackService:
    def __init__(self):
        self.webhook_url = "https://hooks.slack.com/triggers/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"  

    def send_notification(self, case):
        try:
            # Create base message
            message = (
                f"Quick Actions Needed:\n"
                f"• Review case: [Case Link]{case['Case Url']}\n"
                f"• Update any related tickets\n"
                f"• Drive next steps\n"
            )

            # Format total time - just the number
            total_time = f"{case['total_time']:.1f}"

            # Case details owner and status
            case_details = (
                f"Case Details:\n"
                f"• Status: {case['beginning_status_code']}\n"
            )

            # Create payload in the specified format
            payload = {
                "message": message,
                "Case_details":case_details,
                "Total_time": total_time,
                "user": f"{case['agent_login']}@amazon.com"

            }

            # Log the payload for debugging
            logger.info(f"Sending payload to Slack: {payload}")

            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={'Content-Type': 'application/json'}
            )

            # Log the response for debugging
            logger.info(f"Slack response status: {response.status_code}")
            logger.info(f"Slack response text: {response.text}")

            if response.status_code != 200:
                raise ValueError(
                    f"Request to Slack returned an error {response.status_code}, "
                    f"the response is: {response.text}"
                )

            return True, f"Slack notification sent to {case['agent_login']}@amazon.com"

        except Exception as e:
            logger.error(f"Failed to send Slack notification: {str(e)}")
            return False, f"Failed to send Slack notification: {str(e)}"

    def send_bulk_notifications(self, outlier_cases):
        results = []
        for case in outlier_cases:
            success, message = self.send_notification(case)
            results.append({
                'case_id': case['Case ID'],
                'success': success,
                'message': message
            })
        return results
