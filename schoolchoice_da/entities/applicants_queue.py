'''
File: applicants_queue.py
Company: Tether Education Inc.
'''

from schoolchoice_da.entities.applicants import Applicant


class Applicant_Queue:
    def __init__(self,
                capacity: int):
        '''
        Init a Applicant_Queue class.

        Args:
            capacity (int): Queue capacity
        '''
        self.__original_capacity = capacity


    @property
    def capacity(self) -> int:
        return self.__capacity

    @property
    def over_capacity(self) -> int:
        return self.__over_capacity

    def modify_capacity(
            self,
            capacity_to_be_transfered: int) -> None:
        '''
        Modifies the Queue capacity by adding capacity_to_be_transfered

        Args:
            capacity_to_be_transfered (int): Capacity to be added
        '''
        self.__capacity = self.__capacity + capacity_to_be_transfered

    def modify_over_capacity(
            self,
            capacity_to_be_transfered: int):
        '''
        Modifies the Queue over_capacity by adding capacity_to_be_transfered.
        Over capacity is used only in case of forced SE.

        Args:
            capacity_to_be_transfered (int): Capacity to be added
        '''
        self.__over_capacity = self.__over_capacity + capacity_to_be_transfered

    def check_capacity_contraints(self) -> bool:
        '''
        Check if the capacity constraints are fitted.

        Returns:
            bool: False if there are less applicants assigned than capacity.
        '''
        if self.capacity > len(self.vassigned_applicants):
            return False
        else:
            return True

    def add_applicant_to_program(
            self,
            applicant: Applicant):
        '''
        Appends a Applicant instance to vassigned_applicants list

        Args:
            applicant (Applicant): Applicant to append
        '''
        self.vassigned_applicants.append(applicant)

    def add_score_to_program(self, score: float) -> None:
        '''
        Appends a float to vassigned_scores array

        Args:
            score (float): Score to append
        '''
        self.vassigned_scores.append(score)

    def get_cut_off_score(self) -> float:
        '''
        If the queue has capacity and it is filled, returns the highest score
        from vassigned_scores.

        Returns:
            float: Returns 'infty' if the queue has no capacity.
            Return the maximum value in vassigned scores if the there are no
            vacancies left. If there are vacancies left, return 0.
        '''
        # First case: 0 vacancies. -> Return inf
        if (self.capacity == 0):
            return float('inf')

        # Second case: capacity constrains -> Return max score of the array.
        if self.check_capacity_contraints():
            return max(self.vassigned_scores)

        # Third case: no capacity constrains -> Return 0.
        else:
            return 0

    def get_cut_off_applicant(self, cut_off_score: float) -> Applicant:
        '''
        Returns the Applicant instance from vassigned_applicants associated with
        cut_off_score score from vassigned_scores.

        Args:
            cut_off_score (float): Score to search in vassigned_scores.

        Returns:
            Applicant: Applicant asociated with cut_off_score.
        '''
        cut_off_score_index = self.vassigned_scores.index(cut_off_score)
        return self.vassigned_applicants[cut_off_score_index]

    def reassign_applicants_and_scores(
            self,
            new_applicant,
            new_score: float,
            old_applicant) -> None:
        '''
        Replace the position of old_applicant with new_applicant and new_score
        in vassigned_scores and vassigned_applicants

        Args:
            new_applicant (Applicant): Applicant te be added
            new_score (float): Score to be added
            old_applicant (Applicant): Applicant to remove
        '''
        self.vassigned_scores[self.vassigned_applicants.index(
            old_applicant)] = new_score
        self.vassigned_applicants[self.vassigned_applicants.index(
            old_applicant)] = new_applicant

    def reset_assignment(self) -> None:
        '''
        Reset all attributes related to matching.
        '''
        self.__over_capacity = 0
        self.__capacity = self.__original_capacity
        self.vassigned_applicants = []
        self.vassigned_scores = []
        self.tranfer_capacity = False
