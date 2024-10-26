import os
import requests
from flask import Flask, render_template
from identity.flask import Auth
import app_config
#
# Run With flask run -h localhost
#
# Identities --> https://entra.microsoft.com/
# GryTelokk@padel4ever.onmicrosoft.com (Hemmelig****2019)
# JonnyTobiassen@padel4ever.onmicrosoft.com (Hemme****2019)
# AUTHORITY=https://login.microsoftonline.com/a9e120e5-0e5a-43fc-89c1-2e87e9dc90d2
# The following variables are required for the app to run.
# CLIENT_ID=1950eb6f-5995-41ec-b16b-ab22e8eeced4
# CLIENT=MK68Q~vJ6vsuJd3fQx6h9OiZllfWMYfo2.ggobaq

# Your project's redirect URI that you registered in Azure Portal.
# For example: http://localhost:5000/redirect
# REDIRECT_URI=http://localhost:5000/getAToken


__version__ = "0.9.0"  # The version of this sample, for troubleshooting purpose

app = Flask(__name__)
app.config.from_object(app_config)
auth = Auth(
    app,
    authority=os.getenv("AUTHORITY"),
    client_id=os.getenv("CLIENT_ID"),
    client_credential=os.getenv("CLIENT_SECRET"),
    redirect_uri=os.getenv("REDIRECT_URI"),
    oidc_authority=os.getenv("OIDC_AUTHORITY"),
    b2c_tenant_name=os.getenv('B2C_TENANT_NAME'),
    b2c_signup_signin_user_flow=os.getenv('SIGNUPSIGNIN_USER_FLOW'),
    b2c_edit_profile_user_flow=os.getenv('EDITPROFILE_USER_FLOW'),
    b2c_reset_password_user_flow=os.getenv('RESETPASSWORD_USER_FLOW'),
)

@app.route("/")
@auth.login_required(scopes=["User.Read","Group.Read.All"])
def index(*, context):
    #print("Access Token")
    #print(context['access_token'])
    groups = get_user_groups(context['access_token'])
    print(groups)
    print(type(groups))
    upn = context['user'].get('preferred_username')
    print(upn)
    #print(context['user'])
    return render_template(
        'index.html',
        user=context['user'],
        upn=upn,
        groups=groups,
        edit_profile_url=auth.get_edit_profile_url(),
        api_endpoint=os.getenv("ENDPOINT"),
        title=f"Azure Entra AD Authentication POC",
    )

@app.route("/call_api")
@auth.login_required(scopes=os.getenv("SCOPE", "").split())
def call_downstream_api(*, context):
    api_result = requests.get(  # Use access token to call a web api
        os.getenv("ENDPOINT"),
        headers={'Authorization': 'Bearer ' + context['access_token']},
        timeout=30,
    ).json() if context.get('access_token') else "Did you forget to set the SCOPE environment variable?"
    return render_template('display.html', title="API Response", result=api_result)

# Function to get the user's group membership using Microsoft Graph API
def get_user_groups(access_token):
    graph_api_url = "https://graph.microsoft.com/v1.0/me/memberOf"
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    response = requests.get(graph_api_url, headers=headers)

    if response.status_code == 200:
        # Extract group IDs from the response
        groups = response.json().get('value', [])
        group_data = [(group['id'], group['displayName']) for group in groups if 'id' in group and 'displayName' in group]
        #group_ids = [group['id'] for group in groups if 'id' in group]
        return group_data
    else:
        print(f"Error fetching groups: {response.status_code}, {response.text}")
        return []
