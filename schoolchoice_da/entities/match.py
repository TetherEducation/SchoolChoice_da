'''
File: match.py
Company: Tether Education Inc.
'''

from typing import Any, Dict, Tuple
import math

from schoolchoice_da.entities.programs import Program
from schoolchoice_da.entities.applicants import Applicant


class DeferredAcceptanceAlgorithm:
    def __init__(self):
        pass

    def run(self,
            applicants: Dict[int, Applicant],
            programs: Dict[Tuple[int, int], Program]) -> None:
        '''
        Run Deferred Acceptance matching algorithm

        Args:
            applicants (dict): Applicants to be matched
            programs (dict): Programs to be matched
        '''
        remaining_proposals = list(applicants.values())
        while remaining_proposals:
            # Get next proposing applicant
            applicant = remaining_proposals.pop()
            if not applicant.match:
                # We get program and quota id that uses position n
                program_id = applicant.vpostulation[applicant.option_n]
                quota_id = applicant.vquota_id[applicant.option_n]
                try:
                    program = programs[(program_id, quota_id)]
                    rejected_applicant = self.match_applicant_to_program(
                                            applicant,
                                            program)
                except:
                    raise ValueError(f'Error while assigning applicant\
                        :{applicant.id} to program:{(program_id, quota_id)}')
                if rejected_applicant:
                    rejected_applicant.option_n += 1

                    if (rejected_applicant.option_n <
                            len(rejected_applicant.vpostulation)):
                        (DeferredAcceptanceAlgorithm.
                            unmatch_applicant_of_program(
                            rejected_applicant))
                        remaining_proposals.append(rejected_applicant)
                    else:
                        (DeferredAcceptanceAlgorithm
                            .applicant_match_with_None_program(
                            rejected_applicant))

    @staticmethod
    def match_applicant_to_program(
            applicant: Applicant,
            program: Program) -> Any:
        '''
        Match applicant to program and quota if he/she got the score to enter
        the Applicant_Queue, and reject another (or him(her)self) if
        requirements are not met.

        Args:
            applicant (Applicant): Applicant to be match.
            programs (Dict[Tuple[Any, int], Program]): All programs.

        Returns:
            Any: Applicant or None
        '''
        rejected_applicant = None
        # Ocupar cupos que van quedando remanentes en el assignment.
        assigned_applicants = program.get_assignment_type_queue(
                                assignment_type=applicant.special_assignment)
        # Obtener el puntaje del postulante en el programa-quota
        try:
            new_applicant_score = \
                program.get_applicant_score_in_program(applicant)
        except:
            raise ValueError(f'Error while getting score in vpostulation\
            :{applicant.vpostulation} and vquota:{applicant.vquota_id}')
        # Obtener el último puntaje asignado.
        cut_off_score = assigned_applicants.get_cut_off_score()

        # Caso donde no se ha llegado al límite de capacidad.
        if (cut_off_score == 0):
            applicant.match = True
            applicant.assigned_vacancy = program
            assigned_applicants.add_applicant_to_program(applicant)
            assigned_applicants.add_score_to_program(new_applicant_score)

        # Caso de que el programa no tiene cupos (i.e. Capacidad 0)
        elif math.isinf(cut_off_score):
            rejected_applicant = applicant
            rejected_score = new_applicant_score

        # Caso donde se ha llegado al límite de capacidad.
        else:
            # El cutoff le gana a la propuesta
            if (cut_off_score <= new_applicant_score):
                rejected_applicant = applicant
                rejected_score = new_applicant_score

            # La propuesta le gana al cutoff
            elif (new_applicant_score < cut_off_score):
                # Estudiante con el mínimo numero de prioridad
                cut_off_applicant = assigned_applicants.get_cut_off_applicant(
                    cut_off_score)

                applicant.match = True
                applicant.assigned_vacancy = program
                assigned_applicants.reassign_applicants_and_scores(
                    applicant,
                    new_applicant_score,
                    cut_off_applicant)
                rejected_applicant = cut_off_applicant
                rejected_score = cut_off_score
        if rejected_applicant:
            program.add_applicant_to_waitlist(rejected_applicant.id,rejected_score//1)
        
        return rejected_applicant

    @staticmethod
    def unmatch_applicant_of_program(applicant: Applicant) -> None:
        '''
        If applicant was rejected or removed from a program,
        unmatch him/her from the program.

        Args:
            applicant (Applicant): rejected applicant
        '''
        applicant.match = False
        applicant.assigned_vacancy = None

    @staticmethod
    def applicant_match_with_None_program(applicant: Applicant) -> None:
        '''
        Applicants with no match that have no remaining proposals, are matched
        to None program.

        Args:
            applicant (Applicant): rejected applicant of all his/her proposals.
        '''
        applicant.match = True
        applicant.assigned_vacancy = None
