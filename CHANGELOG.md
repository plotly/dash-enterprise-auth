# Change Log for Dash Enterprise Auth
All notable changes to `dash-enterprise-auth` will be documented in this file.
This project adheres to [Semantic Versioning](https://semver.org/).

## [0.2.3] - 2024-05-30
### Fixed
- Fix get_user_date/username with background callback. [#41](https://github.com/plotly/dash-enterprise-auth/pull/41)
- Update error message if run in a notebook cell.

## [0.2.2] - 2024-04-30
### Updated
- Set Flask and Werkzeug upper version bounds to `<3.1`, matching versions with Dash 2.16.1.

### Fixed
- Print traceback on user data requests error. 

## [0.2.1] - 2023-10-13
### Updated
- Add Flask and Werkzeug upper version bounds at `<2.3`. This matches the constraint in Dash v2.13. After we relax the constraint in Dash we will come back and - after testing that it works - relax it here as well.

## [0.2.0] - 2023-08-03
### Updated
- Dropped support for Python versions below 3.6
- Added MIT license

## [0.1.1] - 2023-03-09
### Fixed
- Add back user info from keycloak user info endpoint. [#24](https://github.com/plotly/dash-enterprise-auth/pull/24)

## [0.1.0] - 2022-06-22
### Added
- Add `style` argument to `create_logout_button`. [#22](https://github.com/plotly/dash-enterprise-auth/pull/22)

### Changed
- Use a raw `html.A` to create the logout button if on Dash Enterprise 5. [#22](https://github.com/plotly/dash-enterprise-auth/pull/22)

## [0.0.6] - 2022-05-31
### Added
- Support for Dash Enterprise 5 [#20](https://github.com/plotly/dash-enterprise-auth/pull/20)

## [0.0.5] - 2021-10-04
### Fixed
- Gracefully import dash_core_components whether Dash's version is 1.x or 2.x [#15](https://github.com/plotly/dash-enterprise-auth/pull/15)

## [0.0.4] - 2020-02-05
### Fixed
- Fixed package installation on Python 3.6.[0-4] [#11](https://github.com/plotly/dash-enterprise-auth/pull/11)

## [0.0.3] - 2020-01-08
### Fixed
- Fixed package dependencies on Pypi [#8](https://github.com/plotly/dash-enterprise-auth/pull/8)

## [0.0.2] - 2019-02-08
### Fixed
- Fixed package on Pypi [#3](https://github.com/plotly/dash-enterprise-auth/pull/3)

## [0.0.1] -
### Added
**Initial release**

Adapted from dash-auth

- `create_logout_button` - create a dcc.LogoutButton with the `logout_url` set to the dash-deployment-server logout route.
- `get_username` - get the currently logged in user.
- `get_kerberos_ticket_cache` - Kerberos ticket for environments that supports it.
