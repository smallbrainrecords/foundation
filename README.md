** GETTING STARTED

Creating a README file for the Small Brain Records repository, based on the information provided and the nature of the project, could look something like this:

---

# Small Brain Records Project

## Introduction
Welcome to the Small Brain Records (SBR) Project repository. SBR is an innovative, open-source clinical system designed to revolutionize patient-clinician collaboration in healthcare. Our system focuses on generating machine-learning-friendly labeled data, embedding clinical decision support (CDS) in the right context, and empowering clinicians to deliver outstanding care.

## Features
- **Problem-Task Ontology**: Facilitates meaningful interactions between patients and clinicians.
- **Machine Learning Data Generation**: Automatically generates labeled data for advanced analytics.
- **Context-Aware CDS**: Integrates CDS into the clinical workflow at appropriate times.
- **Audio Recording and Labeling**: Captures and labels clinical encounter audio for enhanced data richness.

## Getting Started
- **Prerequisites**: List the software and hardware requirements.
- **Installation**: Step-by-step guide to set up the SBR project.
- **Configuration**: Instructions for configuring the system to suit specific clinical environments.

## Usage
Detailed instructions on how to use the system in a clinical setting, including case studies or usage scenarios.

## Contribution
Guidelines for contributing to the SBR project, including coding standards, pull request process, and issue reporting.

## Support and Community
Information on how to obtain support, join the community discussions, and collaborate with other users and developers.

## License
This project is licensed under the AGPL-3.0 license - see the [LICENSE](LICENSE) file for details.

## Acknowledgments
Special thanks to the project's lead contributors, advisors, and all who have supported the development of the SBR project.

For more information, visit [smallbrainrecords.org](https://smallbrainrecords.org/).

---

This template provides a general structure for the README file, which can be customized further based on specific details and features of the SBR project.

**Run mysql server using docker enviroment**

`docker run  -d -e MYSQL_ROOT_PASSWORD=root -p 3306:3306 -v D:\Workspace\database\smallbrain:/var/lib/mysql mysql:5.7.22 --sql_mode=""`

**NOTE for updating to Django 1.11 and other dependencies(django-reversion):**
1. Run `python manage.py migrate reversion --fake`
2. Add column `db VARCHAR(191)` to table `reversion_version` 

** TEST COVERAGE **
1. project
2. users_app
3. common
4. emr
5. generic
6. problems_app
7. todo_app
8. data_app
9. a1c_app
10. colons_app
11. goals_app
12. document_app
13. encounters_app
14. inr_app
15. medication_app
16. pain
17. my_story_app
18. project_admin_app
19. site_pages_app

# Admin functions
## Manage users
- Add user
- Edit user
- Deactive user

## Patient Administration
