from email import encoders
from email.message import EmailMessage
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
import logging
import smtplib

def send_mail(message, subject, from_address, to_address, file_name=None, attachment=None, gateway='vdc-relay.us-east-2.a.mail.umich.edu'):

   # Create a multipart email to handle attachments
   msg = MIMEMultipart()

   if type(message) is list:
       message = ''.join(message)

   msg.attach(MIMEText(message, 'plain'))
   msg['Subject'] = subject
   msg['From'] = from_address
   msg['To'] = to_address

   if attachment is not None:
      logging.debug('Now setting up attachment.')
      part = MIMEBase('application','octet-stream')
      part.set_payload(attachment)
      part.add_header(
         'Content-Disposition',
         'attachment',
         filename=file_name)
      encoders.encode_base64(part)
      msg.attach(part)

   try:
      mail_server = smtplib.SMTP(host=gateway, port=25, timeout=90)
      mail_server.send_message(msg)
      logging.debug("successfully passed email message to mail relay.")
   except smtplib.SMTPRecipientsRefused as e:
      logging.error('The following message has invalid recipients: {}'.format(e.recipients))