'''
File: policymaker.py
Company: Tether Education Inc.
'''

from typing import Any, Dict, Tuple, List
import warnings
import sys
import os
import pandas as pd
import numpy as np

from schoolchoice_da.entities.programs import Program
from schoolchoice_da.entities.applicants import Applicant
from schoolchoice_da.entities.match import DeferredAcceptanceAlgorithm


class PolicyMaker:
    '''
    Prepare applicants and programs to be matched under a set of rules.
    '''
    def __init__(
            self,
            vacancies: pd.DataFrame,
            applicants: pd.DataFrame,
            applications: pd.DataFrame,
            priority_profiles: pd.DataFrame,
            quota_order: pd.DataFrame,
            siblings: pd.DataFrame,
            links: pd.DataFrame,
            order: str = 'descending',
            sibling_priority_activation : bool = False,
            linked_postulation_activation : bool = False,
            secured_enrollment_assignment : bool = False,
            forced_secured_enrollment_assignment : bool = False,
            transfer_capacity_activation : bool = False,
            check_inputs : bool =True,
            **kwargs
            ) -> None:
        '''
        Args:
            vacancies (pd.DataFrame): DataFrame with vacancies info.
            applicants (pd.DataFrame): DataFrame with postulants info.
            applications (pd.DataFrame): DataFrame with applications info.
            priority_profiles (pd.DataFrame): DataFrame with priority_profiles
                info.
            quota_order (pd.DataFrame): DataFrame with quota_order info.
            siblings (pd.DataFrame): DataFrame with siblings info.
            links (pd.DataFrame): DataFrame with links info.
            order (str): Orden en el que se corre el algoritmo.
            sibling_priority_activation (bool): Para activar prioridad de hermano
            entre niveles y tipos de asignación (special y Regular.).
            linked_postulation_activation (bool): Para activar postulación en bloque.
            secured_enrollment_assignment (bool): Para activar el uso de secured enrollment.
            forced_secured_enrollment_assignment (bool): Para forzar la asignación
            SE en caso de no haber cupos.
            transfer_capacity_activation (bool): Transfiere vacantes no utilizadas
            desde special a regular assignment.
            check_inputs (bool): Revisa que los dataframes cumplan ciertos requisitos.
        '''
        self._set_rules(order = order,
                sibling_priority_activation = sibling_priority_activation,
                linked_postulation_activation = linked_postulation_activation,
                secured_enrollment_assignment = secured_enrollment_assignment,
                forced_secured_enrollment_assignment = forced_secured_enrollment_assignment,
                transfer_capacity_activation = transfer_capacity_activation,
                check_inputs = check_inputs)

        self.check_inputs(vacancies=vacancies,
                            applicants=applicants,
                            applications=applications,
                            priority_profiles=priority_profiles,
                            quota_order=quota_order,
                            siblings=siblings,
                            links=links)
        self._unpack_priority_profiles(priority_profiles)
        self._unpack_quota_order(quota_order)

        self.algorithm = DeferredAcceptanceAlgorithm()
        applicants = self._add_sibling_and_linked_data(applicants=applicants,
                                                        siblings=siblings,
                                                        links=links)
        applications = self._check_lottery(applications = applications,
                                            applicants = applicants,
                                            siblings = siblings,
                                            **kwargs)
        applications = self._filter_relevant_applications(vacancies = vacancies,
                                            applications = applications,
                                            applicants = applicants)
        applicants = self._add_postulation_data(applicants=applicants,
                                                applications=applications)
        self.applicants_df = self._init_applicants(applicants=applicants)
        self.applicants = self._get_applicants_dict()

        self.programs = self._init_programs_to_dict(vacancies=vacancies)
        self.add_unrelevant_applications_to_waitlist()

        self.ordered_grades = self._get_ordered_grades()
        self.assignment_types = self._get_assignment_types()
        self.first_round = self.ordered_grades[0]
        self.last_round = self.ordered_grades[-1]


    def match_applicants_and_programs(self) -> None:
        '''
        Match applicants and program objects, adjusting sibling priority,
        postulation order, linked postulation, secured enrollment and transfer
        capacity between rounds according to the rules in config.
        '''
        # For each grade
        for grade in self.ordered_grades:
            # Get all programs in such grade
            programs_to_be_assigned = \
                self._prep_programs_for_matching(
                    grade=grade)
            # For each assignment type
            for assignment_type in self.assignment_types:
                # Get all students in such grade and assignment type, modifying
                # them according to conditions specified in config.
                applicants_to_be_assigned = \
                    self._prep_applicants_for_matching(
                        grade=grade,
                        assignment_type=assignment_type)

                # Make grade and assignment_type assignment
                try:
                    self.algorithm.run(applicants=applicants_to_be_assigned,
                                   programs=programs_to_be_assigned)
                except:
                    raise ValueError(f'Error while assigning grade:{grade} and assignment_type:{assignment_type}')

                # Apply transfer capacity or forced secured enrollment
                self._after_round_adjustments(
                    applicants_to_be_assigned=applicants_to_be_assigned,
                    grade=grade,
                    assignment_type=assignment_type)



    def get_results(self) -> pd.DataFrame:
        '''
        Return a DataFrame with the assignation results

        Returns:
            pd.DataFrame: Results df with the fields "applicant_id", "grade_id",
            "program_id", "institution_id", "quota_id", "assigned_score" and
            "priority_profile". If a students is not assigned, the last 5 fields
            are NaN.
        '''
        def yield_applicants():
            for applicant in self.applicants.values():
                dict={'applicant_id':applicant.id}
                dict['grade_id'] = applicant.grade
                prog = applicant.assigned_vacancy
                if prog is None:
                    dict['program_id'] = None
                    dict['institution_id'] = None
                    dict['quota_id'] = None
                    dict['assigned_score'] = None
                    dict['priority_profile'] = None
                else:
                    dict['program_id'] = prog.program_id
                    dict['institution_id'] = prog.institution_id
                    dict['quota_id'] = prog.quota_id
                    dict['assigned_score'] = \
                                prog.get_applicant_score_in_program(applicant)
                    dict['priority_profile'] = \
                                applicant.vpriority_profile[prog.program_id]
                yield dict
        results = pd.DataFrame(yield_applicants())
        return results

    def check_inputs(self,
            vacancies,
            applicants,
            applications,
            priority_profiles,
            quota_order,
            siblings,
            links) -> None:
        '''
        If _check_inputs==True, checks if inputs match certain constrains
        specified in "Inputs_description.md" document.
        '''
        if self._check_inputs:

            for requested_column in ['program_id', 'quota_id',
                    'institution_id', 'grade_id', 'regular_vacancies']:
                if not (requested_column in vacancies.columns):
                    raise KeyError(f'Expected column "{requested_column}" in vacancies DataFrame.')

            for requested_column in ['applicant_id','grade_id']:
                if not (requested_column in applicants.columns):
                    raise KeyError(f'Expected column "{requested_column}" in applicants DataFrame.')
            if len(set(applicants['applicant_id']))!= len(applicants):
                raise ValueError('applicant_id in the applicants database must be unique.')
            if self._secured_enrollment_activation or \
                    self._forced_secured_enrollment_activation:
                if not ('secured_enrollment_program_id' in applicants.columns):
                    raise ValueError('Expected secured_enrollment program_id in applicants DataFrame when secured_enrollment_activation is on. \nTurn it off or add "secured_enrollment_program_id" to applicants DataFrame.')
                if not ('secured_enrollment_quota_id' in applicants.columns):
                    raise ValueError('Expected secured_enrollment quota_id in applicants DataFrame when secured_enrollment_activation is on. \nTurn it off or add "secured_enrollment_quota_id" to applicants DataFrame.')
                #Prevent misleading nan values in secured_enrollment
                applicants['secured_enrollment_program_id'] = \
                    applicants['secured_enrollment_program_id'].fillna(0)
                applicants['secured_enrollment_quota_id'] = \
                    applicants['secured_enrollment_quota_id'].fillna(0)

            for requested_column in ['applicant_id', 'program_id','quota_id',
                'institution_id','ranking_program','priority_profile_program',
                'priority_number_quota']:
                if not (requested_column in applications.columns):
                    raise KeyError(f'Expected column "{requested_column}" in applications DataFrame.')

            if len(set(applications.applicant_id) -
                set(applicants.applicant_id))!=0:
                raise ValueError('There are applications, with applicant_id not registered in applicants DataFrame.')

            if len(set(applicants.applicant_id) -
                set(applications.applicant_id))!=0:
                warnings.warn('There are applicants, without applications.')

            if len(set(applications.program_id) -
                set(vacancies.program_id))!=0:
                raise ValueError('There are applications to programs that do not appear on the vacancies DataFrame.')

            if self._linked_postulation_activation:
                if not isinstance(links,pd.DataFrame):
                    raise ValueError('Expected links dataframe when linked_postulation_activation is on. Turn it off or provide a links DataFrame.')
                if not (('applicant_id' in links.columns) and
                    ('linked_id' in links.columns) and (len(links.columns)==2)):
                    raise ValueError('Unexpected column in links DataFrame. Expected "applicant_id" and "linked_id".')
                if (len(set(links.applicant_id)-set(applicants.applicant_id)) +
                    len(set(links.linked_id) - set(applicants.applicant_id)))!=0:
                    raise ValueError('There are applicant_ids in links DataFrame that are not registred in the applicants DataFrame.')

            for requested_column in ['priority_profile']:
                if not (requested_column in priority_profiles.columns):
                    raise KeyError(f'Expected column "{requested_column}" in priority_profiles DataFrame.')

            if self._sibling_priority_activation:
                if not isinstance(siblings,pd.DataFrame):
                    raise ValueError('Expected siblings DataFrame when sibling_priority_activation is on. Turn it off or provide a siblings DataFrame.')
                if not (('applicant_id' in siblings.columns) and
                    ('sibling_id' in siblings.columns) and
                    (len(siblings.columns)==2)):
                    raise ValueError('Unexpected column in siblings DataFrame. Expected "applicant_id" and "sibling_id".')
                if (len(set(siblings.applicant_id)-set(applicants.applicant_id)) +
                    len(set(siblings.sibling_id) - set(applicants.applicant_id)))!=0:
                    raise ValueError('There are applicant_ids in siblings DataFrame \
                    that are not registred in the applicants DataFrame.')
                if not ('priority_profile_sibling_transition' in
                    priority_profiles.columns):
                    raise KeyError(f'Expected column "priority_profile_sibling_transition" in priority_profiles DataFrame when sibling_priority_activation is on. Turn it off or add "priority_profile_sibling_transition" to priority_profiles DataFrame.')

            for requested_column in ['priority_profile']:
                if not (requested_column in quota_order.columns):
                    raise KeyError(f'Expected column "{requested_column}" in quota_order DataFrame.')
            if self._secured_enrollment_activation or \
                    self._forced_secured_enrollment_activation:
                for requested_column in ['secured_enrollment_indicator',
                    'secured_enrollment_quota_id_criteria',
                    'secured_enrollment_quota_id_value']:
                    if not (requested_column in quota_order.columns):
                        raise KeyError(f'Expected column "{requested_column}" in quota_order DataFrame when secured_enrollment_activation is on. Turn it off or add "{requested_column}" to priority_profiles DataFrame.')
                if not quota_order['secured_enrollment_quota_id_criteria'].isin(
                    ['<', '<=', '>', '>=', '=', '!=', '==', 'le', 'leq',
                    'ge', 'geq', 'eq', 'neq']).all():
                    raise ValueError('Unexpected value in "secured_enrollment_quota_id_criteria" column of the quota_order dataframe. Use strings such as "<", "<=", ">", ">=", "=", "!=", "==", "le", "leq", "ge", "geq", "eq" or "neq".')


    def _init_applicants(
            self,
            applicants: pd.DataFrame) -> pd.DataFrame:
        '''
        Init all applicants objects in a df

        Args:
            applicants (pd.DataFrame): raw applicants dataframe

        Returns:
            pd.DataFrame: applicants df ready to used in matching
        '''
        self.applicant_characteristics = [col for col in applicants.columns \
            if 'applicant_characteristic' in col]

        applicant_objects = [self._init_applicant_object(**row) for
                            row in applicants.to_dict(orient="records")]
        applicants['applicant_object'] = applicant_objects

        return applicants

    def _init_programs_to_dict(
            self,
            vacancies: pd.DataFrame) -> Dict:
        '''
        Init all program objects and place them in a dict indexed by their
        program id and quota_id.

        Args:
            vacancies (pd.DataFrame): raw vacancies dataframe

        Returns:
            Dict[(int,int): Program] :{(program_id,quota_id) : program_object}
            programs dict ready to be used in matching.
        '''
        programs_dict = {}
        self.special_assignment_cols = [col for col in vacancies.columns \
            if 'special' in col]
        vacancies = vacancies.rename(columns={ \
            'regular_vacancies':'regular_capacity'})
        for row in vacancies.to_dict(orient="records"):
            p_object = self._init_program_object(row)
            programs_dict[(row['program_id'], row['quota_id'])] = p_object
        return programs_dict

    def _get_applicants_dict(
            self,
            query: str = '') -> Dict[int, Applicant]:
        '''
        Returns the applicants as dict indexed by their applicant id according
        to a query.

        Returns:
            Dict[int, Applicant]: {Applicant_id: Applicant_object}
        '''

        applicants_df = self.applicants_df
        if len(query) > 0:
            applicants_df = applicants_df.query(query)
        return (applicants_df[['applicant_id', 'applicant_object']]
                .set_index('applicant_id')
                .to_dict(orient='dict'))['applicant_object']

    def _set_rules(
            self,
            **kwargs) -> None:
        '''
        Set rules of the school assignment according to parameters provided
        '''
        self._order = kwargs['order']

        self._sibling_priority_activation = \
            kwargs['sibling_priority_activation']
        self._linked_postulation_activation = \
            kwargs['linked_postulation_activation']
        self._transfer_capacity_activation = \
            kwargs['transfer_capacity_activation']
        self._secured_enrollment_activation = \
            kwargs['secured_enrollment_assignment']
        self._forced_secured_enrollment_activation = \
            kwargs['forced_secured_enrollment_assignment']
        self._check_inputs = \
            kwargs['check_inputs']

    def _get_ordered_grades(self) -> List:
        '''
        Get the set of grades ordered dependign on the rules

        Returns:
            List: ordered grades
        '''
        grades = list(set(self.applicants_df.grade_id))
        if self._order == 'descending':
            grades.sort(reverse=True)
        else:
            grades.sort()
        return grades

    def _get_assignment_types(self) -> List[int]:
        '''
        Get the types of assignment for run the algorithm. The order to process
        special assignment is 1 to n, and then 0.

        Returns:
            List[int]: assignment_types
        '''
        assignment_types = [int(column.split('_')[1])
            for column in self.special_assignment_cols]
        assignment_types.sort()
        return assignment_types+[0]

    def _prep_programs_for_matching(
            self,
            grade: int) -> Dict[int, Applicant]:
        '''
        Select programs in a certain grade from programs dict.

        Args:
            grade (int)
        '''
        return {k:prog for k,prog in self.programs.items() if prog.grade_id==grade}

    def _prep_applicants_for_matching(
            self,
            grade: int,
            assignment_type: int) -> Dict[int, Applicant]:
        '''
        Considering what happen in last rounds, prepare the subset of
        applicants to be matched.

        Args:
            grade (int)
            assignment_type (int)
        '''
        # Select all applicants in such grade and assignment type
        if 'special_assignment' in self.applicants_df.columns:
            q1 = (f'((grade_id == {grade}) &'
                  f' (special_assignment == {assignment_type}))')
        else:
            q1 = (f'(grade_id == {grade})')
        stus_to_be_assigned_df = self.applicants_df.query(q1)
        if grade != self.first_round:
            # Apply Dynamic sibling priority
            if (self._sibling_priority_activation):
                stus_to_be_assigned_df.loc[:, 'applicant_object'].apply(
                  self._apply_sib_priority)
            # Apply Linked postulation reorder
            if (self._linked_postulation_activation):
                stus_to_be_assigned_df.loc[:, 'applicant_object'].apply(
                    self._apply_linked_reorder)
        # Get the right quota postulation order
        stus_to_be_assigned_df.loc[:, 'applicant_object'].apply(
            self._check_quota_postulation_order)
        # Apply Secured Enrollment adjustments
        if (self._secured_enrollment_activation):
            stus_to_be_assigned_se_df = stus_to_be_assigned_df[
                    stus_to_be_assigned_df.se_program_id!=0]
            stus_to_be_assigned_se_df.loc[:, 'applicant_object'].apply(
                lambda applicant: \
                applicant.set_secured_place_as_last_postulation())
        return self._get_applicants_dict(query=q1)

    def _after_round_adjustments(
            self,
            applicants_to_be_assigned: Dict[int, Applicant],
            grade: int,
            assignment_type: int) -> None:
        '''
        Considering what happen in the last round, transfer capacities
        and force secured enrollment

        Args:
            applicants_to_be_assigned (Dict[int, Applicant])
            grade (int)
            assignment_type (int)
        '''
        if (assignment_type != 0) and (self._transfer_capacity_activation):
            # Apply transfer capacity
            self._reasign_programs_capacity(current_grade=grade,
                                            assignment_type=assignment_type)

        if (self._forced_secured_enrollment_activation):
            # For each student
            for _,applicant in applicants_to_be_assigned.items():
                # If it has SE
                if applicant._has_SE():
                    # Apply forced SE
                    self._match_secured_enrollment_applicant(applicant)


    def _apply_sib_priority(
            self,
            applicant: Applicant) -> None:
        '''
        Search all the siblings of a applicant. If they are matched in schools
        that are inside the postulation of the applicant, change vpriorities.

        Args:
            applicant (Applicant)
        '''
        if ~applicant.match:
            if len(applicant.vsiblings) > 0:
                schools_with_sib = set()
                for sibling_id in applicant.vsiblings:  # Check all the siblings
                    # Get the sibling from applicants graph
                    sibling = self.applicants[sibling_id]
                    # Check if the sibling is alredy matched to some program.
                    if (sibling.match) and (sibling.assigned_vacancy is not None):
                        # Give me the school where the sibling was accepted and
                        # append it to the array.
                        schools_with_sib.add(
                            sibling.assigned_vacancy.institution_id)

                applicant_schools_ids = applicant.vinstitution_id
                # Return the indexes of applicant_schools_ids where there is
                # coincidence with schools_with_sib
                indexes_to_change_sibling_priority = [i for i, id in
                    enumerate(applicant_schools_ids) if id in schools_with_sib]

                # We loop over all the indexes to change priority
                for index in indexes_to_change_sibling_priority:
                    applicant.reasign_priority_profile(index,
                        self.priority_profile_transition)


    def _apply_linked_reorder(
            self,
            applicant: Applicant) -> None:
        '''
        Check if a applicant has linked applicants that were match to
        a program, and reorder the postulation of the applicant, considering
        his/her preferences and the schools that coincide with their
        assigned linked applicants.

        Args:
            applicant (Applicant)
        '''
        if not applicant.match:
            if len(applicant.vlinks) > 0:
                schools_with_linked = set()
                linked_grades = set()
                # Check all the linked postulations
                for link_applicant_id in applicant.vlinks:
                    # Get the linked applicant from applicants graph
                    linked = self.applicants[link_applicant_id]
                    # Check if the linked is alredy matched to some program.
                    if (linked.match) and (linked.assigned_vacancy is not None):
                        # Give me the school where the linked was accepted and
                        # append it to the array.
                        schools_with_linked.add(
                                    linked.assigned_vacancy.institution_id)
                        linked_grades.add(
                                    linked.assigned_vacancy.grade_id)

                #Translate the array vpostulation from program_id to institution_id
                applicant_schools_ids = applicant.vinstitution_id
                linked_grades = list(linked_grades)

                # Indexes of applicant_schools_ids where there is coincidence
                # with schools_with_linked, ordered from more to least preferred
                indexes_to_put_in_first_place = [i for i, id in \
                    enumerate(applicant_schools_ids) if id in schools_with_linked]


                # Indexes of applicant_schools_ids where there is NO coincidence
                # with schools_with_linked, ordered from more to least preferred
                indexes_to_put_after_first_place = [i for i in \
                    range(len(applicant_schools_ids)) if i \
                    not in indexes_to_put_in_first_place]

                new_postulation_arrays_order = indexes_to_put_in_first_place + \
                                                indexes_to_put_after_first_place
                # Reorder postulation in applicant object
                applicant.reorder_postulation(linked_grades,
                                            new_postulation_arrays_order)



    def _check_quota_postulation_order(
            self,
            applicant: Applicant) -> None:
        '''
        Check the postulation order of student and correct it following the
        info from self.quota_order_dict. This modifies the quota postulation
        order, but not the program postulation order

        Args:
            applicant (Applicant)
        '''
        if ~applicant.match:
            # If the applicant has a priority that needs reorder
            if not set(applicant.vpriority_profile.values()).isdisjoint(
                self.quota_order_dict_keys):
                #Get the programs where the student has such priority
                tuples_to_modify = [(program_id,priority_profiles)
                    for program_id,priority_profiles
                    in applicant.vpriority_profile.items()
                    if priority_profiles in self.quota_order_dict_keys]

                for program_id,priority_profile in tuples_to_modify:
                    # Loop over all programs that need reorder
                    # priority_profile = applicant.vpriority_profile[program_id]
                    pp_quota_order_list = self.quota_order_dict[priority_profile].copy()
                    secured_enrollment_indicator = \
                        (applicant.se_program_id==program_id)
                    # Check criteria
                    for pp_dict in pp_quota_order_list:
                        # Check SE criteria
                        if self._secured_enrollment_activation:
                            if pp_dict['secured_enrollment_indicator'] \
                                !=secured_enrollment_indicator:
                                continue
                            if secured_enrollment_indicator:
                                if not applicant.check_attribute_criteria(
                                    attribute = 'se_quota_id',
                                    criteria =
                                        pp_dict['secured_enrollment_quota_id_criteria'],
                                    value =
                                        pp_dict['secured_enrollment_quota_id_value']):
                                    continue
                        # Check other characteristics criteria
                        aux_attribute_criteria=True
                        for applicant_characteristic in \
                            self.quota_order_characteristics:
                            if not applicant.check_attribute_criteria(
                                attribute = applicant_characteristic,
                                criteria =
                                    pp_dict[f'{applicant_characteristic}_criteria'],
                                value =
                                    pp_dict[f'{applicant_characteristic}_value']):
                                aux_attribute_criteria=False
                                break
                        if not aux_attribute_criteria:
                            continue
                        # If satisfies all criterias, reorder the quotas
                        applicant.reorder_postulation_by_quota(
                            program_id=program_id,
                            ordered_quotas=pp_dict['ordered_quotas'])


    def _reasign_programs_capacity(
            self,
            current_grade: int,
            assignment_type: int) -> None:
        '''
        Transfer capacity from assignment type n to regular assignment.

        Args:
            current_grade (int): int
            assignment_type (int): int
        '''
        for program in self.programs.values():
            if (program.grade_id != current_grade):
                continue

            capacity_to_transfer = \
                program.get_capacity_to_transfer(
                                from_assignment_type=assignment_type)
            if (capacity_to_transfer == 0):
                continue
            program.transfer_capacity(capacity_to_transfer=capacity_to_transfer)

    def _match_secured_enrollment_applicant(
            self,
            applicant: Applicant) -> None:
        '''
        Description: match a applicant with secure enrollment to his/her
        secured option in case he/she didn't match any program.
        This method changes atributtes of Applicant and Program Object.

        Args:
            applicant (Applicant)
        '''
        # Applicant match to None program
        if (applicant.match) & (applicant.assigned_vacancy is None):
            secured_program = self.programs[(applicant.se_program_id,
                                             applicant.se_quota_id)]

            secured_program._force_secured_enrollment_match(
                applicant)
            applicant.match = True
            applicant.assigned_vacancy = secured_program

    def _init_applicant_object(self, **row: Dict) -> Applicant:
        '''
        From applicants dataframe row, init an applicant object.

        Args:
            row (Dict): Row of applicants dataframe

        Returns:
            Applicant: applicant object
        '''
        applicant_characteristics = \
            {key:row[key] for key in self.applicant_characteristics}
        applicant = Applicant(
                      applicant_characteristics=applicant_characteristics,
                      **row)
        return applicant


    def _init_program_object(self, row: Dict) -> Program:
        '''
        From vacancies dataframe row, init a program object.

        Args:
            row (pd.DataFrame): Row of programs dataframe

        Returns:
            Program: program object
        '''
        special_vacancies = \
            {key:row[key] for key in self.special_assignment_cols}
        prog = Program(special_vacancies=special_vacancies,
                       **row)
        return prog

    def _add_sibling_and_linked_data(
            self,
            applicants: pd.DataFrame,
            siblings: pd.DataFrame,
            links: pd.DataFrame) -> pd.DataFrame:
        '''
        Group by applicant_id, siblings and linked data
        in list to merge it with applicants data

        Args:
            applicants(pd.DataFrame): Applicants df
            siblings(pd.DataFrame): Siblings df
            links(pd.DataFrame): Links df

        Returns:
            applicants(pd.DataFrame): Updated version of the DataFrame
        '''
        #We use a numpy level groupby.agg(list)
        def gb_list(df,col_a,col_b):
            keys, values = df.sort_values(col_a).values.T
            ukeys, index = np.unique(keys, True)
            arrays = np.split(values, index[1:])
            df2 = pd.DataFrame(
                {col_a:ukeys, col_b:[list(a) for a in arrays]}).set_index(col_a)
            return df2

        if not isinstance(links,pd.DataFrame):
            links = pd.DataFrame({'applicant_id':[],'linked_id':[]})
        if len(links)==0:
            links_gb = links.rename(
                columns={'linked_id': 'links'}).set_index('applicant_id')
        else:
            links_gb = gb_list(links,'applicant_id','links')


        if not isinstance(siblings,pd.DataFrame):
            siblings = pd.DataFrame({'applicant_id':[],'sibling_id':[]})
        if len(siblings)==0:
            siblings_gb = siblings.rename(
                columns={'sibling_id': 'siblings'}).set_index('applicant_id')
        else:
            siblings_gb = gb_list(siblings,'applicant_id','siblings')

        applicants = applicants.join(links_gb,on='applicant_id')
        applicants = applicants.join(siblings_gb,on='applicant_id')


        for col_label in ['links', 'siblings']:
            applicants[col_label] = applicants[col_label].apply(lambda d: \
                d if isinstance(d, list) else [])

        return applicants

    def _filter_relevant_applications(
            self,
            applicants: pd.DataFrame,
            applications: pd.DataFrame,
            vacancies: pd.DataFrame) -> None:
        '''
        Remove applications to quotas without vacancies.
        Avoid to delete SE programs.

        Args:
            applicants(pd.DataFrame): Applicants df
            applications(pd.DataFrame): Applications df
            vacancies(pd.DataFrame): Vacancies df

        Returns:
            applications(pd.DataFrame): Updated version of the DataFrame
        '''
        # Get all postulations to programs with more than 0 vacancies
        relevant_vacancies = \
            vacancies.loc[vacancies[[col for col in vacancies.columns
            if '_vacancies' in col]].sum(axis=1)>0][['program_id','quota_id']]
        applications = \
            pd.merge(applications,relevant_vacancies,
            on=['program_id','quota_id'],how='left',indicator='Relevant')
        applications['Relevant'] = (applications['Relevant']=='both')
        # If forced_secured_enrollment is on, get all postulations to SE programs
        if self._secured_enrollment_activation or \
                self._forced_secured_enrollment_activation:
            SE_applicants = \
                applicants.loc[applicants.secured_enrollment_program_id!=0][
                ['applicant_id','secured_enrollment_program_id']].rename(
                columns={'secured_enrollment_program_id':'program_id'})
            applications = \
                pd.merge(applications,SE_applicants,
                on=['applicant_id','program_id'],how='left',indicator='SE')
            applications['Relevant'] = \
                (applications['Relevant'] | (applications['SE']=='both'))
            applications = applications.drop(columns=['SE'])

        # Keep postulations if any of the two conditions above are meet
        self.unrelevant_applications = applications.loc[~applications.Relevant][['applicant_id','program_id','quota_id','priority_number_quota']]
        applications = applications.loc[applications.Relevant]
        applications = applications.drop(columns=['Relevant'])

        return applications

    def add_unrelevant_applications_to_waitlist(self):
        for _,(applicant_id,program_id,quota_id,priority_number_quota) in self.unrelevant_applications.iterrows():
            self.programs[(program_id,quota_id)].add_applicant_to_waitlist(applicant_id,priority_number_quota)
        del self.unrelevant_applications


    def _check_lottery(
            self,
            applicants: pd.DataFrame,
            applications: pd.DataFrame,
            siblings: pd.DataFrame,
            **kwargs) -> None:
        '''
        If Applications does not have 'lottery_number_quota' columns, call
        lottery_maker module.

        Args:
            applicants(pd.DataFrame): Applicants df
            applications(pd.DataFrame): Applications df
            siblings(pd.DataFrame): Siblings df

        Returns:
            applications(pd.DataFrame): Updated version of the DataFrame
        '''
        if not ('lottery_number_quota' in applications.columns):

            try:
                from cb_lottery_maker import lottery_maker
            except:
                raise ImportError('Could not find module lottery_maker. Applications DataFrame did not have a "lottery_number_quota" column, so we tried to import lottery_maker. Provide such column or install the lottery_maker package.')

            class HiddenPrints:
                def __enter__(self):
                    self._original_stdout = sys.stdout
                    sys.stdout = open(os.devnull, 'w')

                def __exit__(self, exc_type, exc_val, exc_tb):
                    sys.stdout.close()
                    sys.stdout = self._original_stdout

            with HiddenPrints():
                applications = lottery_maker(applicants = applicants,
                            applications = applications,
                            siblings = siblings,
                            order_applicants = False,
                            **kwargs)

        return applications


    def _add_postulation_data(
            self,
            applicants: pd.DataFrame,
            applications: pd.DataFrame) -> pd.DataFrame:
        '''
        Transform and groupby applications data to merge it with
        applicants data. Before we unpack them, we make sure they have all
        requested columns.


        Args:
            applicants(pd.DataFrame): Applicants df
            applications(pd.DataFrame): Applications df

        Returns:
            applicants(pd.DataFrame): Updated version of the DataFrame
        '''
        #We use a numpy level groupby.agg(list)
        def gb_list(df):
            aux_values = df.values.T
            other_col_names = df.columns[1:]
            keys = aux_values[0,:]
            try:
                keys = keys.astype(int)
            except:
                keys = keys.astype(str)
            values = aux_values[1:,:]
            ukeys, index = np.unique(keys, return_index=True, axis=0)
            # split data columns according to those indices
            arrays = np.split(values, index[1:], axis=1)
            idx = pd.Index(ukeys.T,name='applicant_id')
            list_agg_vals = dict()
            for tup in zip(*arrays, other_col_names):
                col_vals = tup[:-1] # first entries are the subarrays from above
                col_name = tup[-1]  # last entry is data-column name

                list_agg_vals[col_name] = col_vals

            df2 = pd.DataFrame(data=list_agg_vals,index=idx)
            return df2


        #Postulations for same program are ordered by quota id. This is then
        # modified by prep_applicants_for_matching considering the quota_order df
        applications = applications.sort_values(['applicant_id',
                                                    'ranking_program',
                                                    'quota_id'])

        applications = applications.rename(\
            columns={'program_id':'vpostulation',
                        'lottery_number_quota':'vpostulation_scores',
                        'priority_number_quota':'vpriorities',
                        'institution_id':'vinstitution_id',
                        'quota_id':'vquota_id',
                        'priority_profile_program':'vpriority_profile'})

        if applications.vpostulation.isna().sum()!=0:
            raise ValueError('There are Nan program ids in applications dataframe')
        if applications.vpostulation_scores.isna().sum()!=0:
            raise ValueError('There are Nan lottery numbers in applications dataframe')

        int_vcolumns = ['vpostulation',
                    'vinstitution_id',
                    'vpriorities',
                    'vquota_id',
                    'vpriority_profile']
        float_vcolumns = ['vpostulation_scores']
        applications = applications[['applicant_id']+float_vcolumns+int_vcolumns]
        grouped_int = gb_list(applications[['applicant_id']+int_vcolumns])
        grouped_float = gb_list(applications[['applicant_id']+float_vcolumns])

        applicants = applicants.join(grouped_int,on='applicant_id')
        applicants = applicants.join(grouped_float,on='applicant_id')

        applicants = applicants.rename(columns={ \
                'secured_enrollment_program_id':'se_program_id',
                'secured_enrollment_quota_id':'se_quota_id'})


        return applicants


    def _unpack_priority_profiles(
            self,
            priority_profiles: pd.DataFrame) -> None:
        '''
        Save the number of quotas and priority transitions from the
        priority profiles dataframe.

        Args:
            priority_profiles(pd.DataFrame): Priority_profiles df
        '''
        self.n_quotas = len([col for col in priority_profiles.columns \
            if 'priority_q' in col])
        if self.n_quotas==0:
            raise ValueError('There must be at least one "priority_qi" column in priority profiles DataFrame. If you do not need quotas, add a quota "0".')

        self.priority_profile_transition = \
            priority_profiles.set_index(['priority_profile']).to_dict()


    def _unpack_quota_order(
            self,
            quota_order: pd.DataFrame) -> None:
        '''
        Save the rules for reordering the quota postulation from the
        quota order dataframe.

        Args:
            quota_order(pd.DataFrame): Quota_order df
        '''
        # Restructure from quota_order df into dict[key:list(dict)] structure
        # priority_profile_key: [ {'secured_enrollment_indicator': bool,
        #             'secured_enrollment_quota_id_criteria': str,
        #             'secured_enrollment_quota_id_value': val,
        #             'applicant_characteristic_i_criteria': str,
        #             'applicant_characteristic_i_value': val,
        #             'ordered_quotas': List(int)} ]
        # NOTE: There could be more than one row per priority_profile in quota_order

        aux_quota_order = quota_order.set_index(['priority_profile'],append=True)
        self.quota_order_dict = \
            {pp:aux_quota_order.xs(pp, level=1).to_dict('records')
            for pp in list(set(aux_quota_order.index.get_level_values(1)))}
        # quota_order_dict_keys is needed to process every student, thus it is
        # more efficient to calculate it once and save it.
        self.quota_order_dict_keys = set(self.quota_order_dict.keys())

        # Save quota_order_characteristics column names.
        # Make sure these columns follow the appropriate format.
        self.quota_order_characteristics=list(set(col.rsplit('_', 1)[0]
            for col in quota_order if 'applicant_characteristic' in col))
        for applicant_characteristic in self.quota_order_characteristics:
            if not quota_order[f'{applicant_characteristic}_criteria'].isin(
                ['<', '<=', '>', '>=', '=', '!=', '==', 'le', 'leq',
                'ge', 'geq', 'eq', 'neq']).all():
                raise ValueError(f'Unexpected value in {applicant_characteristic} criteria in quota_order DataFrame. Use strings such as "<", "<=", ">", ">=", "=", "!=", "==", "le", "leq", "ge", "geq", "eq" or "neq".')

        # There must be at least one quota
        order_columns=list(set(col
            for col in quota_order if 'order' in col))
        if len(order_columns)==0:
            raise ValueError('There must be at least one "order_qi" column in quota_order DataFrame. If you do not need quotas, add a quota "0".')

        for pp,pp_quota_order_list in self.quota_order_dict.items():
            for pp_dict in pp_quota_order_list:
                aux_dict = {int(key[-1]):pp_dict[key]
                    for key in order_columns}

                sorted_quotas = [key
                    for (key,value) in sorted(aux_dict.items(), key=lambda x: x[1])]

                # Add 'ordered_quotas':list
                pp_dict.update({'ordered_quotas':sorted_quotas})
                # Delete 'order_qi' keys
                for key in order_columns:
                    pp_dict.pop(key)


    def reset_matching(self):
        '''
        Resets both programs and applicants
        '''
        for program in self.programs.values():
            program._reset_matching_attributes()
        for applicant in self.applicants.values():
            applicant._reset_matching_attributes()
