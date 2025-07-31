import boto3
import logging

logger = logging.getLogger(__name__)
ses_client = boto3.client('ses', region_name='us-east-2')

def send_ses_notification(outlier_cases):
    try:
        html_content = create_html_content(outlier_cases)
        text_content = create_text_content(outlier_cases)

        response = ses_client.send_email(
            Source='rlck@amazon.com',
            Destination={
                'ToAddresses': ['avirmani@amazon.com']
                # 'ToAddresses': ['email1@example.com', 'email2@example.com'] multiple
            },
            Message={
                'Subject': {
                    'Data': 'TWFL WAF Outlier Cases Alert',
                    'Charset': 'UTF-8'
                },
                'Body': {
                    'Html': {
                        'Data': html_content,
                        'Charset': 'UTF-8'
                    },
                    'Text': {
                        'Data': text_content,
                        'Charset': 'UTF-8'
                    }
                }
            }
        )
        return True, f"Email sent successfully. MessageId: {response['MessageId']}"
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        return False, f"Failed to send email: {str(e)}"

def create_html_content(outlier_cases):
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta http-equiv="Content-Type" content="text/html charset=UTF-8" />
    </head>
    <body style="font-family: Arial, sans-serif;">
        <h2 style="color: #232f3e;">TWFL WAF Outlier Cases Alert</h2>
        <p>Your attention is needed on the case , currently at TWFL >  3.5-days threshold for WAF. Quick review and next steps implementation would help maintain our service quality and customer satisfaction:</p>
        <table style="border-collapse: collapse; width: 100%; border: 1px solid #ddd;">
            <thead>
                <tr style="background-color: #232f3e; color: white;">
                    <th style="padding: 12px; border: 1px solid #ddd;">Case ID</th>
                    <th style="padding: 12px; border: 1px solid #ddd;">Agent Login</th>
                    <th style="padding: 12px; border: 1px solid #ddd;">Ops Site</th>
                    <th style="padding: 12px; border: 1px solid #ddd;">Total Time</th>
                    <th style="padding: 12px; border: 1px solid #ddd;">Status Code</th>
                </tr>
            </thead>
            <tbody>
    """

    for case in outlier_cases:
        case_url = case['Case Url']
        case_id = case['Case ID']

        html_content += f"""
            <tr>
                <td style="padding: 12px; border: 1px solid #ddd;">
                    <a href="{case_url}" style="color: #0066c0; text-decoration: underline;">
                        {case_id}
                    </a>
                </td>
                <td style="padding: 12px; border: 1px solid #ddd;">{case['agent_login']}</td>
                <td style="padding: 12px; border: 1px solid #ddd;">{case['ops_site']}</td>
                <td style="padding: 12px; border: 1px solid #ddd;">{case['total_time']:.1f}</td>
                <td style="padding: 12px; border: 1px solid #ddd;">{case['beginning_status_code']}</td>
            </tr>
        """

    html_content += """
            </tbody>
        </table>
        <br>
        <p style="font-size: 12px; color: #666;">
            Note: Click on the Case ID numbers above to view the cases in Command Center.
        </p>
    </body>
    </html>
    """
    
    return html_content

def create_text_content(outlier_cases):
    text_content = "TWFL WAF Outlier Cases Alert\n\n"
    text_content += "Your attention is needed on the case , currently at TWFL >  3.5-days threshold for WAF. Quick review and next steps implementation would help maintain our service quality and customer satisfaction:\n\n"
    
    for case in outlier_cases:
        text_content += f"Case ID: {case['Case ID']} - {case['Case Url']}\n"
        text_content += f"Agent: {case['agent_login']}, Site: {case['ops_site']}, Time: {case['total_time']:.1f}s\n\n"
    
    return text_content
