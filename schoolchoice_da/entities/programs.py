'''
File: programs.py
Company: Tether Education Inc.
'''

from schoolchoice_da.entities.applicants_queue import Applicant_Queue
from schoolchoice_da.entities.applicants import Applicant



class Program:
    def __init__(self,
                 program_id: int,
                 quota_id: int,
                 institution_id: int,
                 grade_id: int,
                 regular_capacity: int,
                 special_vacancies = {},
                 **kwargs):
        '''
        Init a Program instance. A program is defined by its program and
        quota id.

        Args:
            program_id (str):
            quota_id (int):
            institution_id (str):
            grade_id (int):
            regular_capacity (int):
            special_vacancies (dict): Dict with keys names "special_i_vacancies"
            for i =1,...,n. Values must be ints representing a capacity.
        '''
        self.__program_id = program_id
        self.__institution_id = institution_id
        self.__grade_id = grade_id
        self.__quota_id = quota_id
        self.regular_assignment = Applicant_Queue(regular_capacity)

        self._unpack_special_vacancies(special_vacancies)

        self._reset_matching_attributes()

    @property
    def program_id(self) -> int:
        return self.__program_id

    @property
    def institution_id(self) -> int:
        return self.__institution_id

    @property
    def grade_id(self) -> int:
        return self.__grade_id

    @property
    def quota_id(self) -> int:
        return self.__quota_id

    def get_applicant_score_in_program(
            self,
            applicant: Applicant) -> float:
        '''
        Receive a applicant and search the score
        associated for that applicant to self.

        Args:
            applicant (Applicant): Applicant instance

        Returns:
            float: score associated to the program
        '''

        # Score of the applicant at (program , quota_id)
        # (could be selection score or lotery number)
        applicant_postulation_score = applicant.vpostulation_scores[(self.program_id,self.quota_id)]

        # Priority of the applicant at (program , quota_id)
        applicant_priority = applicant.vpriorities[(self.program_id,self.quota_id)]

        return applicant_postulation_score + applicant_priority

    def get_assignment_type_queue(
            self,
            assignment_type: int):
        '''
        Returns the corresponding applicants queue depending on assignment_type.

        Args:
            assignment_type (int): Number indicating assignment_type

        Returns:
            attr (Applicants_Queue): Applicants_Queue instance
        '''
        if assignment_type==0:
            return self.regular_assignment
        else:
            return getattr(self, f'special_{assignment_type}_assignment')

    def get_capacity_to_transfer(self,
            from_assignment_type: int):
        '''
        Depending on capacity constraints from the selected assignment_type,
        modifies the capacity of such queue and returns the modified capacity.

        Args:
            from_assignment_type (int): Number indicating assignment_type from
            where to substract capacity

        Returns:
            capacity_to_be_transfered (int): Capacity to be transfered
        '''
        assignment = self.get_assignment_type_queue(
                            assignment_type=from_assignment_type)
        capacity_to_be_transfered = 0
        if (not assignment.check_capacity_contraints()):
            self.tranfer_capacity = True
            assignment.transfer_capacity = True
            capacity_to_be_transfered = \
                (assignment.capacity - len(assignment.vassigned_applicants))

            assignment.modify_capacity(-capacity_to_be_transfered)
        return capacity_to_be_transfered

    def transfer_capacity(
            self,
            capacity_to_transfer: int):
        '''
        Transfers capacity to regular assignment.

        Args:
            capacity_to_transfer (int): Capacity to be transfered.
        '''
        self.receive_capacity = True
        self.regular_assignment.receive_capacity = True
        self.regular_assignment.modify_capacity(capacity_to_transfer)

    def _force_secured_enrollment_match(
            self,
            secured_applicant: Applicant) -> None:
        '''
        Take an Applicant an his/her score from and move to assignment,
        leaving an indicator that over_capacity of Program was modified.

        Args:
            secured_applicant (Applicant):
                Applicant to be forced into assignment
        '''
        self.over_capacity = True
        capacity_to_be_transfered = 1

        assignment = self.get_assignment_type_queue(
                        assignment_type=secured_applicant.special_assignment)
        # Modify over capacity.
        assignment.modify_over_capacity(capacity_to_be_transfered)

        # Identify applicant score
        applicant_score = self.get_applicant_score_in_program(
                            secured_applicant)

        # Add applicant to corresponding assignment
        assignment.add_applicant_to_program(secured_applicant)
        assignment.add_score_to_program(applicant_score)

        #Remove applicant from waitlist
        self.waitlist_dict.pop(secured_applicant.id,None)

    def _reset_matching_attributes(self) -> None:
        '''
        Reset all attributes related to matching.
        '''
        self.tranfer_capacity = False
        self.receive_capacity = False
        self.over_capacity = False
        self.regular_assignment.reset_assignment()
        self.waitlist_dict = {}
        for i in self.special_assignment_types:
            getattr(self, f'special_{i}_assignment').reset_assignment()


    def _unpack_special_vacancies(
            self,
            special_vacancies) -> None:
        '''
        Description: Set all special_vacancies as queue atributes.

        Args:
            special_vacancies (pd.Series): Series with row names
            "special_i_vacancies" for i =0,...,n. Each row value must
            be an int representing a capacity.
        '''
        if len(special_vacancies)>0:
            self.special_assignment_types = [keys.split('_')[1]
                for keys in special_vacancies.keys()]
            for key,i in zip(special_vacancies.keys(),
                                        self.special_assignment_types):
                setattr(self, f'special_{i}_assignment', Applicant_Queue(special_vacancies[key]))
        else:
            self.special_assignment_types = []


    def add_applicant_to_waitlist(
        self,
        applicant_id,
        priority_number_quota: float) -> None:
        '''
        Add Applicant to waitlist

        Args:
            applicant_id: applicant_id to be added
            priority_number_quota (float): Score
        '''
        self.waitlist_dict.update({applicant_id:priority_number_quota})
