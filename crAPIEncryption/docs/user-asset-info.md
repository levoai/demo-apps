crAPI | Users & Assets Info
================

crAPI comes pre-populated with a few users, and other assets associated with the users. This info will be helpful in the [Hack Pad][Hack Pad] exercises where you need to exploit several [vulnerabilities][0].

### User Info

Use the info below to login to crAPI

| UserID                   | Password     | Role          | Username     | Phone Number |
| ------------------------ | :----------- | ------------- | ------------ | ------------ |
| victim.one@example.com   | Victim1One   | ROLE_USER     | Victim One   | 4156895423   |
| victim.two@example.com   | Victim2Two   | ROLE_USER     | Victim Two   | 9876570006   |
| hacker@darkweb.com       | Hack3r$$$    | ROLE_USER     | Hacker       | 7000070007   |
| mechanic.one@example.com | Mechanic1One | ROLE_MECHANIC | Mechanic One | 9051892421   |
| mechanic.two@example.com | Mechanic2Two | ROLE_MECHANIC | Mechanic Two | 8056897231   |
| admin.one@example.com    | Admin1One    | ROLE_ADMIN    | Admin One    | 6052895429   |
| admin.two@example.com    | Admin2Two    | ROLE_ADMIN    | Admin Two    | 4258221234   |

### User's Vehicle UUID

Below are UUIDs of vehicles that belong to users:

| UserID                 | Vehicle UUID                         | VIN               |
| ---------------------- | ------------------------------------ | ----------------- |
| victim.one@example.com | 649acfac-10ea-43b3-907f-752e86eff2b6 | 0BZCX25UTBJ987271 |
| victim.two@example.com | 8b9edbde-d74d-4773-8c9f-adb65c6056fc | 4NGPB83BRXL720409 |
| hacker@darkweb.com     | abac4018-5a38-466c-ab7f-361908afeab6 | 5JTGZ48TPYP220157 |
| admin.one@example.com  | edee0263-0179-4d9e-9ab5-90e4e64afb34 | 5NPDH4AE0DH213924 |
| admin.two@example.com  | 836fe80c-02f9-4fc0-8fbd-fcdf637bb9c2 | JH4KA96633C000632 |

### User's Service Reports

Below are IDs of vehicle service reports filed by the users:

| UserID                 | Service Report IDs |
| ---------------------- | ------------------ |
| victim.one@example.com | 1, & 2             |
| victim.two@example.com | 3, & 4             |
| hacker@darkweb.com     | 5, & 6             |
| admin.one@example.com  | 7, & 8             |
| admin.two@example.com  | 9, & 10            |

### User's Previous Shop Orders

Below are IDs of shop orders placed by the users:

| UserID                   | Order IDs          |
| ----------------------   | ------------------ |
| victim.one@example.com   | 1, & 2             |
| victim.two@example.com   | 3, & 4             |
| hacker@darkweb.com       | No Orders          |
| admin.one@example.com    | 5, & 6             |
| admin.two@example.com    | 7, & 8             |
| mechanic.one@example.com | 9, & 10            |
| mechanic.two@example.com | 11, & 12           |


Please note that these orders are pre-populated on the first start of crAPI. If you manipulate these orders via the shop API endpoints, these order IDs may not be consistent.

[0]: ./challenges.md
[Hack Pad]: ./hackpad.md
