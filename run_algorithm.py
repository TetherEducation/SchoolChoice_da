# Template to run schoolchoice_da algorithm
#
# 1.- Make sure schoolchoice_da package is installed. Follow README.md if needed.
# 2.- Make sure you have all needed files according to the Inputs_description.md document.
# 3.a- If your files are in a single folder in your local enviroment, you only need to modify the Inputs_Path variable.
# 3.b- If not, edit this script in order to have access to your input files.
# 4.- Add/edit the optional arguments
# 5.a- If you want your results to be saved in a local folder, you only need to modify the Outputs_Path variable.
# 5.b- If not, edit this script in order to save your results as needed.
# 6.- Run "run_algorithm.py" script.

from schoolchoice_da import da
import pandas as pd

Inputs_Path = "C:\\Users\\...\\inputs\\"
Outputs_Path = "C:\\Users\\...\\outputs\\"



vacancies = pd.read_csv(Inputs_Path + 'vacancies.csv')
applicants = pd.read_csv(Inputs_Path + 'applicants.csv')
applications = pd.read_csv(Inputs_Path + 'applications.csv')
priority_profiles = pd.read_csv(Inputs_Path + 'priority_profiles.csv')
quota_order = pd.read_csv(Inputs_Path + 'quota_order.csv')
siblings = pd.read_csv(Inputs_Path + 'siblings.csv')
links = pd.read_csv(Inputs_Path + 'links.csv')

arguments = {'sibling_priority_activation' :        False,
            'linked_postulation_activation' :       False,
            'secured_enrollment_assignment' :       False,
            'forced_secured_enrollment_assignment' :False,
            'transfer_capacity_activation' :        False}

results = da(vacancies=vacancies,
            applicants=applicants,
            applications=applications,
            priority_profiles=priority_profiles,
            quota_order=quota_order,
            siblings=siblings,
            links=links,
            **arguments)

results.to_csv(Outputs_Path+'results.csv',index=False)
