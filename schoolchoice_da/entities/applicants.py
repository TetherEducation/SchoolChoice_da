'''
File: applicant.py
Company: Tether Education Inc.
'''

from typing import Any, List, Dict
import numpy as np
import pandas as pd
import operator



class Applicant():
    eval_dict={'<':operator.lt,
                '<=':operator.le,
                '>':operator.gt,
                '>=':operator.ge,
                '=':operator.eq,
                '!=':operator.ne,
                '==':operator.eq,
                'le':operator.lt,
                'leq':operator.le,
                'ge':operator.gt,
                'geq':operator.ge,
                'eq':operator.eq,
                'neq':operator.ne}

    secured_enrollment_priority = 0

    def __init__(self,
                 applicant_id: Any,
                 grade_id: int,
                 links: np.ndarray,
                 siblings: np.ndarray,
                 vpostulation: np.ndarray,
                 vpostulation_scores: np.ndarray,
                 vinstitution_id: np.ndarray,
                 vpriorities: np.ndarray,
                 vquota_id: np.ndarray,
                 vpriority_profile: np.ndarray,
                 special_assignment: int = 0,
                 se_program_id: Any = 0,
                 se_quota_id: Any = 0,
                 applicant_characteristics = {},
                 **kwargs):
        '''
        Init a Applicant instance.

        Args:
            applicant_id (Any): Hashable
            grade_id (int):
            links (Array[Any]): Array of applicant_id
            siblings (Array[Any]): Array of applicant_id
            vpostulation (Array[Any]): Array of program_id where to apply
            vpostulation_scores (Array[float]): Array of scores
            vinstitution_id (Array[Any]): Array of institution_id
            vpriorities (Array[int]): Array of priorities
            vquota_id (Array[int]): Array of quotas associated with vpostulation
            vpriority_profile (Array[int]): Array of priorities associated with
                vpostulation
            special_assignment (int): Indicate the applicants type of assignment
            se_program_id (int): 0 or program_id
            se_quota_id (int): 0 or quota_id
            applicant_characteristics (dict, optional): Dictionary with
                aditional characteristics needed for the assignment
        '''
        self.__id = applicant_id
        self.__special_assignment = special_assignment
        self.__grade = grade_id
        self.__vsiblings = siblings
        self.__vlinks = links
        self.__original_vpostulation = vpostulation
        self.__original_vinstitution_id = vinstitution_id
        self.__original_vquota_id = vquota_id
        self.__se_program_id = se_program_id if (se_program_id!=0 and se_program_id!='') else None
        self.__se_quota_id = se_quota_id if (se_program_id!=0 and se_program_id!='') else None
        self._unpack_priorities_and_scores(vpostulation_scores,vpriorities,vpriority_profile)

        if len(applicant_characteristics)>0:
            self._unpack_applicant_characteristics(applicant_characteristics)

        self._reset_matching_attributes()


    @property
    def id(self):
        return self.__id

    @property
    def special_assignment(self):
        return self.__special_assignment

    @property
    def grade(self):
        return self.__grade

    @property
    def vsiblings(self):
        return self.__vsiblings

    @property
    def vlinks(self):
        return self.__vlinks

    @property
    def se_program_id(self):
        return self.__se_program_id

    @property
    def se_quota_id(self):
        return self.__se_quota_id


    def modify_original_vpostulation_scores(
            self,
            program_id,quota_id,lottery) -> None:
        '''
        Modifies the original_vpostulation_scores and sets lottery as new score

        Args:
            program_id (int): Program to be modified
            quota_id (int): Quota to be modified
            lottery (float): New score
        '''
        self.__original_vpostulation_scores[(program_id,quota_id)] = lottery


    def _unpack_priorities_and_scores(
            self,
            vpostulation_scores,
            vpriorities,
            vpriority_profile):
        if isinstance(self.__original_vpostulation,float):
            self.__original_vpostulation_scores = dict()
            self.__original_vpriorities = dict()
            self.__original_vpriority_profile = dict()
        else:
            self.__original_vpostulation_scores = {(pid,qid):score for pid,qid,score in zip(self.__original_vpostulation,self.__original_vquota_id,vpostulation_scores)}
            self.__original_vpriorities = {(pid,qid):priority for pid,qid,priority in zip(self.__original_vpostulation,self.__original_vquota_id,vpriorities)}
            self.__original_vpriority_profile = dict(zip(self.__original_vpostulation,vpriority_profile))



    def _unpack_applicant_characteristics(
            self,
            applicant_characteristics) -> None:
        '''
        Description: Set all applicant_characteristics as attributes

        Args:
            applicant_characteristics (dict): Each key,value pair represents a
                applicant characteristic
        '''
        for key,value in applicant_characteristics.items():
            setattr(self, key, value)


    def _reset_matching_attributes(self) -> None:
        '''
        Reset all attributes related to matching algorithm.
        '''
        self.option_n = 0
        self.linked_postulation = False
        self.linked_postulation_bool = False
        self.cut_postulation = False
        self.reassign_quota_order = False
        self.assigned_vacancy = None
        if isinstance(self.__original_vpostulation,float):
            self.match = True
            self.vpostulation = []
            self.vinstitution_id = []
            self.vquota_id = []
            self.vpostulation_scores = dict()
            self.vpriorities = dict()
            self.vpriority_profile = dict()
            self.dynamic_priority = None
        else:
            self.match = False
            self.vpostulation = self.__original_vpostulation.copy()
            self.vinstitution_id = self.__original_vinstitution_id.copy()
            self.vquota_id = self.__original_vquota_id.copy()
            self.vpostulation_scores = self.__original_vpostulation_scores.copy()
            self.vpriorities = self.__original_vpriorities.copy()
            self.vpriority_profile = self.__original_vpriority_profile.copy()
            self.dynamic_priority = [False]*len(self.vpostulation)


    def reasign_priority_profile(
            self,
            index: int,
            transition: Dict) -> None:
        '''
        Modifies the priority profile in the index position using transition.

        Args:
            index (int): Index to modify
            transition (Dict): Dictionary with transitions according to
                priority profiles. This transition comes from priority_profiles
                DataFrame.
        '''
        program_id = self.vpostulation[index]
        quota_id = self.vquota_id[index]
        priority_profile = self.vpriority_profile[program_id]
        new_priority_profile = \
            transition['priority_profile_sibling_transition'][priority_profile]
        self.vpriority_profile[program_id] = new_priority_profile
        self.vpriorities[(program_id,quota_id)] = \
            transition[f'priority_q{quota_id}'][new_priority_profile]
        self.dynamic_priority[index] = True

    def reorder_postulation(
            self,
            linked_grades: List,
            new_postulation_arrays_order: List) -> None:
        '''
        Description: Save the linked_grades in self, save the original
        postulation arrays and reorder them.

        Args:
            linked_grades (List): List with all the linked grades
            new_postulation_arrays_order (List): List with indexes to
            reorder postulation arrays.
        '''
        self.linked_postulation_bool = True
        # Keep a register of the linked levels
        self.linked_grades = linked_grades

        # Reorder postulation arrays
        self.vpostulation = \
            self.vpostulation[new_postulation_arrays_order]
        self.vinstitution_id = \
            self.vinstitution_id[new_postulation_arrays_order]
        self.vquota_id = \
            self.vquota_id[new_postulation_arrays_order]

    def set_secured_place_as_last_postulation(self) -> None:
        '''
        Drop the postulation arrays elements that are after secured enrollment.
        Also set the priority of (SE_program,SE_quota) postulation to the predefined
        SE priority.
        Raise if the postulation is not found
        '''
        self.cut_postulation = True
        try:
            last_post_index = \
                np.where(self.vpostulation == self.se_program_id)[0][-1]
        except:
            raise ValueError(f'Applicant {self.id} does not have the SE program {self.se_program_id} in vpostulation.')
        #The +1 ensures that [:last_index] includes the SE program
        last_index = last_post_index+1
        # Keep only the postulation that are at the left of the
        # last secured program index
        self.vpostulation = self.vpostulation[:last_index]
        self.vinstitution_id = self.vinstitution_id[:last_index]
        self.vquota_id = self.vquota_id[:last_index]

        try:
            self.vpriorities[(self.se_program_id,self.se_quota_id)] = self.secured_enrollment_priority
        except:
            raise ValueError(f'Applicant {self.id} does not have the pair (SE_program,SE_quota) ({self.se_program_id},{self.se_quota_id}) in vpostulation.')


    def check_attribute_criteria(self,
            attribute:str,
            criteria:str,
            value) -> bool:
        '''
        Evaluates the criteria string and compares self.atrribute
        with value.

        Returns:
            bool: True if criteria is met.
        '''
        attr = getattr(self, attribute)
        return self.eval_dict[criteria](attr,value)

    def reorder_postulation_by_quota(self,
            program_id: Any,
            ordered_quotas: List):
        '''
        Reorders the postulation to program_id using the order_df dataframe.
        Modifies vpriorities, vpostulation_scores and vquota_id.

        Args:
            program_id (Any): Hashable present in vpostulation
            ordered_quotas (List): List containing the proper quota order.
        '''
        indexes_to_modify = np.where(self.vpostulation==program_id)[0]
        if len(indexes_to_modify)!=len(ordered_quotas):
            postulation_quotas = self.vquota_id[indexes_to_modify]
            self.vquota_id[indexes_to_modify]=[q for q in ordered_quotas if q in postulation_quotas]
        else:
            self.vquota_id[indexes_to_modify]=ordered_quotas



    def _has_SE(self):
        '''
        True if the Applicant has a non null SE program id.
        '''
        return (not (self.se_program_id is None))
