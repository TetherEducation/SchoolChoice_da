'''
File: da.py
Company: Tether Education Inc.
'''

from schoolchoice_da.entities.policymaker import PolicyMaker


def da(vacancies, applicants, applications, priority_profiles, quota_order,
        siblings=None,
        links=None,
        order= 'descending',
        sibling_priority_activation= False,
        linked_postulation_activation= False,
        secured_enrollment_assignment= False,
        forced_secured_enrollment_assignment= False,
        transfer_capacity_activation= False,
        check_inputs=True,
        **kwargs):
    '''
    Main method for the application of Deferred Acceptance Algorithm
    '''

    print('*******************************************************')
    print('*******************************************************')
    print('>>> SCHOOL MATCHING ALGORITHM  <<<')
    print('>>> TETHER EDUCATION INC.  <<<')
    print('*******************************************************')
    print('*******************************************************')

    print('*******************************************************')
    print('*******************************************************')
    print('>>> CONFIGURATION DETAILS <<<')
    print('Order: ', order)
    print('Dynamic Sibling Priority: ', sibling_priority_activation)
    print('Family Application: ', linked_postulation_activation)
    print('Students with Secured Enrollment: ', secured_enrollment_assignment)
    print('Forced Secured Enrollment: ', forced_secured_enrollment_assignment)
    print('Transfer Capacity: ', transfer_capacity_activation)
    print('*******************************************************')
    print('*******************************************************')

    print('>> Loading and preparing data')

    policy_maker = PolicyMaker(vacancies = vacancies,
        applicants = applicants,
        applications = applications,
        priority_profiles = priority_profiles,
        quota_order = quota_order,
        siblings = siblings,
        links = links,
        order= order,
        sibling_priority_activation = sibling_priority_activation,
        linked_postulation_activation = linked_postulation_activation,
        secured_enrollment_assignment = secured_enrollment_assignment,
        forced_secured_enrollment_assignment = forced_secured_enrollment_assignment,
        transfer_capacity_activation = transfer_capacity_activation,
        check_inputs = check_inputs,
        **kwargs)

    print('>> Starting matching algorithm')
    policy_maker.match_applicants_and_programs()
    print('>> Getting results')

    output = policy_maker.get_results()

    print('*******************************************************')
    print('*******************************************************')
    print('>>> SCHOOL MATCHING ALGORITHM   <<<')
    print('>>> TETHER EDUCATION INC.  <<<')
    print('*******************************************************')
    print('*******************************************************')
    return output
