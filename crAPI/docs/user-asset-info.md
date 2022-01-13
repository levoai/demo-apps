crAPI | Users & Assets Info
================

crAPI comes pre-populated with a few users, and other assets associated with the users. This info will be helpful in the [Hack Pad][Hack Pad] exercises where you need to exploit several [vulnerabilities][0].

### User Info

Use the info below to login to crAPI

| UserID                 | Password   | Username   | Phone Number |
| ---------------------- | :--------- | ---------- | ------------ |
| victim.one@example.com | Victim1One | Victim One | 4156895423   |
| victim.two@example.com | Victim2Two | Victim Two | 9876570006   |
| hacker@darkweb.com     | Hack3r$$$  | Hacker     | 7000070007   |

### User's Vehicle UUID

Below are UUIDs of vechicles that belong to users:

| UserID                 | Vehicle UUID                         | VIN               |
| ---------------------- | ------------------------------------ | ----------------- |
| victim.one@example.com | 649acfac-10ea-43b3-907f-752e86eff2b6 | 0BZCX25UTBJ987271 |
| victim.two@example.com | 8b9edbde-d74d-4773-8c9f-adb65c6056fc | 4NGPB83BRXL720409 |
| hacker@darkweb.com     | abac4018-5a38-466c-ab7f-361908afeab6 | 5JTGZ48TPYP220157 |

### User's Service Reports

Below are IDs of vehicle service reports filed by the users:

| UserID                 | Service Report IDs |
| ---------------------- | ------------------ |
| victim.one@example.com | 1, & 2             |
| victim.two@example.com | 3, & 4             |
| hacker@darkweb.com     | 5, & 6             |

### User's Previous Shop Orders

Below are IDs of shop orders placed by the users:

| UserID                 | Service Report IDs |
| ---------------------- | ------------------ |
| victim.one@example.com | 1, & 2             |
| victim.two@example.com | 3, & 4             |
| hacker@darkweb.com     | No Orders          |

Please note that these orders are pre-poluated on the first start of crAPI. If you manipulate these orders via the shop API endpoints, these order IDs may not be consistent.

[0]: ./challenges.md
[Hack Pad]: ./hackpad.md
