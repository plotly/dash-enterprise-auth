# Dash Enterprise Auth

Authentication for apps deployed to [Dash Enterprise](https://plotly.com/dash)

Learn more at https://dash.plotly.com/dash-enterprise/app-authentication

<div align="center">
  <a href="https://dash.plotly.com/project-maintenance">
    <img src="https://dash.plotly.com/assets/images/maintained-by-plotly.png" width="400px" alt="Maintained by Plotly">
  </a>
</div>

```py
import dash_enterprise_auth as auth

@callback(...)
def private_data(...):
    username = auth.get_username()
    if username:
        return get_view_for_user(username)
    else:
        return public_view()
```
