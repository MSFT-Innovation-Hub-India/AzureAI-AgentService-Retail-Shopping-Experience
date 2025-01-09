#!/usr/bin/env python3
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
import os
from dotenv import load_dotenv
load_dotenv()

class DefaultConfig:
    """ Bot Configuration """
    PORT = 3978
    APP_ID = ""
    APP_PASSWORD = ""
    APP_TYPE = "MultiTenant"
    APP_TENANTID = "" # leave empty for MultiTenant

    az_agentic_ai_service_connection_string=os.getenv("az_agentic_ai_service_connection_string")
    az_application_insights_key=os.getenv("az_application_insights_key")
    az_logic_app_url=os.getenv("az_logic_app_url")
    az_assistant_id = os.getenv("az_assistant_id")