from flask import Flask, request, render_template
import pandas as pd
import boto3
import logging
# from email_service import send_ses_notification  # Commented out email service
from slack_service import SlackService

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize Slack service
slack_service = SlackService()

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
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process_file():
    try:
        if 'file' not in request.files:
            return render_template('error.html', error='No file uploaded'), 400

        file = request.files['file']
        if file.filename == '':
            return render_template('error.html', error='No file selected'), 400

        if not file.filename.endswith('.csv'):
            return render_template('error.html', error='Please upload a CSV file'), 400

        # Process the file
        outlier_cases = process_csv_data(file)

        # Comment out email notification part
        """
        email_status = None
        if outlier_cases:
            email_sent, email_message = send_ses_notification(outlier_cases)
            email_status = {
                'success': email_sent,
                'message': email_message
            }
        """
        
        # Only handle Slack notifications
        slack_results = []
        if outlier_cases:
            logger.info(f"Sending Slack notifications for {len(outlier_cases)} cases")
            slack_results = slack_service.send_bulk_notifications(outlier_cases)
            logger.info(f"Slack notifications completed. Results: {len(slack_results)} notifications sent")

        return render_template('results.html', 
                             outlier_cases=outlier_cases,
                             # email_status=email_status,  # Commented out
                             slack_results=slack_results)

    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        return render_template('error.html', error=str(e)), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
