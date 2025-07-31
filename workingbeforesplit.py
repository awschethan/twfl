from flask import Flask, request, render_template_string
import pandas as pd
import boto3
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# AWS SES configuration
ses_client = boto3.client('ses', region_name='us-east-2')

def send_ses_notification(outlier_cases):
    try:
        # Create HTML table for email with clickable links
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta http-equiv="Content-Type" content="text/html charset=UTF-8" />
        </head>
        <body style="font-family: Arial, sans-serif;">
            <h2 style="color: #232f3e;">TWFL WAF Outlier Cases Alert</h2>
            <p>The following cases have total_time exceeding 3.5 seconds:</p>
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

        # Create plain text version as fallback
        text_content = "TWFL WAF Outlier Cases Alert\n\n"
        text_content += "The following cases have total_time exceeding 3.5 seconds:\n\n"
        for case in outlier_cases:
            text_content += f"Case ID: {case['Case ID']} - {case['Case Url']}\n"
            text_content += f"Agent: {case['agent_login']}, Site: {case['ops_site']}, Time: {case['total_time']:.1f}s\n\n"

        response = ses_client.send_email(
            Source='rlck@amazon.com',  # Replace with your verified email
            Destination={
                'ToAddresses': ['avirmani@amazon.com']  # Replace with recipient email
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
def process_csv_data(file):
    try:
        df = pd.read_csv(file)
        outliers = df[df['total_time'] > 3.5]
        return outliers.to_dict('records') if not outliers.empty else []
    except Exception as e:
        logger.error(f"Error processing CSV data: {str(e)}")
        raise

@app.route('/', methods=['GET'])
def index():
    html = '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>CSV File Upload</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .upload-form { max-width: 500px; margin: 0 auto; }
                .submit-btn { 
                    margin-top: 20px;
                    padding: 10px 20px;
                    background-color: #232f3e;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                }
                .submit-btn:hover {
                    background-color: #1a2532;
                }
            </style>
        </head>
        <body>
            <div class="upload-form">
                <h2>Upload TWFL WAF Case Data CSV</h2>
                <form action="/process" method="post" enctype="multipart/form-data">
                    <input type="file" name="file" accept=".csv" required>
                    <br>
                    <input type="submit" value="Upload and Process" class="submit-btn">
                </form>
            </div>
        </body>
        </html>
    '''
    return render_template_string(html)

@app.route('/process', methods=['POST'])
def process_file():
    try:
        if 'file' not in request.files:
            return 'No file uploaded', 400
        
        file = request.files['file']
        if file.filename == '':
            return 'No file selected', 400
        
        if not file.filename.endswith('.csv'):
            return 'Please upload a CSV file', 400

        # Process the file
        outlier_cases = process_csv_data(file)
        
        # Send email if there are outliers
        email_status = None
        if outlier_cases:
            email_sent, email_message = send_ses_notification(outlier_cases)
            email_status = f"""
                <div class="email-status" style="margin: 20px 0; padding: 10px; border-radius: 4px; 
                    background-color: {'#dff0d8' if email_sent else '#f2dede'}; 
                    color: {'#3c763d' if email_sent else '#a94442'};">
                    {email_message}
                </div>
            """
        
        # Create formatted HTML response
        html_response = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h2 {{ color: #232f3e; }}
                .summary {{ 
                    background-color: #f8f9fa;
                    padding: 10px;
                    border-radius: 5px;
                    margin-bottom: 20px;
                }}
                table {{
                    border-collapse: collapse;
                    width: 100%;
                    margin-top: 20px;
                }}
                th, td {{
                    border: 1px solid #ddd;
                    padding: 8px;
                    text-align: left;
                }}
                th {{
                    background-color: #232f3e;
                    color: white;
                }}
                tr:nth-child(even) {{
                    background-color: #f2f2f2;
                }}
                .case-link {{
                    color: #0066c0;
                    text-decoration: none;
                }}
                .case-link:hover {{
                    text-decoration: underline;
                }}
                .back-btn {{
                    display: inline-block;
                    margin-top: 20px;
                    padding: 10px 20px;
                    background-color: #232f3e;
                    color: white;
                    text-decoration: none;
                    border-radius: 4px;
                }}
                .back-btn:hover {{
                    background-color: #1a2532;
                }}
            </style>
        </head>
        <body>
            <h2>Analysis Results</h2>
            {email_status if email_status else ''}
            <div class="summary">
                Found {len(outlier_cases)} cases with total_time > 3.5 seconds
            </div>
        """
        
        if outlier_cases:
            html_response += """
                <table>
                    <tr>
                        <th>Case ID</th>
                        <th>Agent Login</th>
                        <th>Ops Site</th>
                        <th>Total Time</th>
                        <th>Status Code</th>
                        <th>Start Date</th>
                        <th>Resolution Date</th>
                    </tr>
            """
            
            for case in outlier_cases:
                html_response += f"""
                    <tr>
                        <td><a href="{case['Case Url']}" class="case-link" target="_blank">{case['Case ID']}</a></td>
                        <td>{case['agent_login']}</td>
                        <td>{case['ops_site']}</td>
                        <td>{case['total_time']:.1f}</td>
                        <td>{case['beginning_status_code']}</td>
                        <td>{case['start_date']}</td>
                        <td>{case['case_resolution_cal_date']}</td>
                    </tr>
                """
            
            html_response += "</table>"
        
        html_response += """
            <a href="/" class="back-btn">Back to Upload</a>
        </body>
        </html>
        """
        
        return html_response

    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        return f"""
            <html>
            <body style="font-family: Arial, sans-serif; margin: 20px;">
                <div style="color: #721c24; background-color: #f8d7da; padding: 10px; border-radius: 4px;">
                    Error processing file: {str(e)}
                </div>
                <a href="/" style="display: inline-block; margin-top: 20px; padding: 10px 20px; 
                    background-color: #232f3e; color: white; text-decoration: none; border-radius: 4px;">
                    Back to Upload
                </a>
            </body>
            </html>
        """, 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
