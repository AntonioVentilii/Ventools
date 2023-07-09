# -*- coding: utf-8 -*-
"""
Provides functions for creating and displaying email messages and meeting invitations.
This module uses the win32com library to interact with Microsoft Outlook.

Author: Antonio Ventilii
"""

import pythoncom
import win32com.client as win32
from premailer import transform


def create_email(html_body, subject: str = None, recipient: str = None, copy_recipient: str = None,
                 attachments: list[str] = None, auto_send: bool = False, transform_body: bool = False):
    """
    Creates and displays an email message.

    Args:
        html_body (str): The HTML body of the email.
        subject (str, optional): The subject of the email. Defaults to None.
        recipient (str, optional): The recipient of the email. Defaults to None.
        copy_recipient (str, optional): The copy recipient of the email. Defaults to None.
        attachments (list[str], optional): A list of file paths for attachments. Defaults to None.
        auto_send (bool, optional): Determines whether the email should be sent automatically. Defaults to False.
        transform_body (bool, optional): Determines whether the HTML body should be transformed using premailer.
                                         Defaults to False.
    """
    if attachments is None:
        attachments = []

    outlook = win32.Dispatch('outlook.application', pythoncom.CoInitialize())
    mail = outlook.CreateItem(0)
    mail.To = recipient or ''
    mail.CC = copy_recipient or ''
    mail.Subject = subject or ''

    if transform_body:
        # Transform the HTML body using premailer for pseudo-classes
        html_body = transform(html_body, exclude_pseudoclasses=False)

    mail.HTMLBody = html_body

    for attachment in attachments:
        mail.Attachments.Add(attachment)

    if auto_send and recipient is not None and recipient != '':
        mail.Send()
    else:
        mail.Display()


def create_meeting(subject: str = None, recipient: str = None, start=None, end=None, all_day: bool = False,
                   auto_send: bool = False):
    """
    Creates and displays a meeting invitation.

    Args:
        subject (str, optional): The subject of the meeting. Defaults to None.
        recipient (str, optional): The recipient of the meeting invitation. Defaults to None.
        start (datetime, optional): The start datetime of the meeting. Defaults to None.
        end (datetime, optional): The end datetime of the meeting. Defaults to None.
        all_day (bool, optional): Determines whether the meeting is an all-day event. Defaults to False.
        auto_send (bool, optional): Determines whether the meeting invitation should be sent automatically.
                                    Defaults to False.
    """
    outlook = win32.Dispatch('outlook.application', pythoncom.CoInitialize())
    appt = outlook.CreateItem(1)  # AppointmentItem
    appt.Start = start  # yyyy-MM-dd hh:mm

    if end:
        appt.End = end

    appt.AllDayEvent = all_day
    appt.Subject = subject or ''

    # appt.Duration = 60  # In minutes (60 Minutes)
    # appt.Location = "Location Name"
    appt.MeetingStatus = 1  # 1 - olMeeting; Changing the appointment to meeting. Only after changing the meeting status recipients can be added
    appt.Recipients.Add(recipient or '')  # Don't end ; as delimiter

    # Set Pattern, to recur every day, for the next 5 days
    # pattern = appt.GetRecurrencePattern()
    # pattern.RecurrenceType = 0
    # pattern.Occurrences = "5"

    appt.Display()

    if auto_send and recipient is not None and recipient != '':
        appt.Send()
