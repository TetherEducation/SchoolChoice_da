from unittest import TestCase, main
from faker import Faker
from schoolchoice_da.entities import Applicant, Program, DeferredAcceptanceAlgorithm
import random
import numpy as np


class DeferredAcceptanceAlgorithmTest(TestCase):
    """API logic test suite"""

    def setUp(self) -> None:
        self.fake = Faker()
        Faker.seed()
        self.program_id = str(self.fake.uuid4())

        self.grade_id = self.fake.random_int(0,20)
        self.quota_id = self.fake.random_digit()
        self.institution_id = str(self.fake.uuid4())
        self.regular_capacity = self.fake.random_int(1,20)

        self.program = Program(program_id = self.program_id,
                                grade_id = self.grade_id,
                                quota_id = self.quota_id,
                                institution_id = self.institution_id,
                                regular_capacity = self.regular_capacity,
                                special_vacancies = {})

        postulation_length = self.fake.random_int(1,10)
        self.app_score = random.random()
        self.app_priority = 1
        self.app_profile = self.fake.random_digit()
        self.applicant = Applicant(applicant_id = str(self.fake.uuid4()),
                                    special_assignment = 0,
                                    grade_id = self.grade_id,
                                    links = [],
                                    siblings = [],
                                    vpostulation = np.array([str(self.fake.uuid4()) for i in range(postulation_length)]+[self.program_id]),
                                    vpostulation_scores = np.array([random.random() for i in range(postulation_length)]+[self.app_score]),
                                    vinstitution_id = np.array(self.fake.random_choices(elements=[str(self.fake.uuid4()) for i in range(postulation_length)],length=postulation_length)+[self.institution_id]),
                                    vpriorities = np.array([self.fake.random_digit() for i in range(postulation_length)]+[self.app_priority]),
                                    vquota_id = np.array([self.fake.random_digit() for i in range(postulation_length)]+[self.quota_id]),
                                    vpriority_profile = np.array([self.fake.random_digit() for i in range(postulation_length)]+[self.app_profile]))
        self.algorithm = DeferredAcceptanceAlgorithm()

    def test_unmatch_applicant_of_program(self):
        self.algorithm.unmatch_applicant_of_program(self.applicant)

        self.assertFalse(self.applicant.match)
        self.assertIsNone(self.applicant.assigned_vacancy)

    def test_applicant_match_with_None_program(self):
        self.algorithm.applicant_match_with_None_program(self.applicant)

        self.assertTrue(self.applicant.match)
        self.assertIsNone(self.applicant.assigned_vacancy)

    def test_match_score_error(self):
        temp_applicant = Applicant(applicant_id = str(self.fake.uuid4()),
                                    special_assignment = 0,
                                    grade_id = self.grade_id,
                                    links = [],
                                    siblings = [],
                                    vpostulation = np.array([str(self.fake.uuid4())]),
                                    vpostulation_scores = np.array([random.random()]),
                                    vinstitution_id = np.array([str(self.fake.uuid4())]),
                                    vpriorities = np.array([self.fake.random_digit()]),
                                    vquota_id = np.array([self.fake.random_digit()]),
                                    vpriority_profile = np.array([self.fake.random_digit()]))

        self.assertRaises(ValueError,self.algorithm.match_applicant_to_program,temp_applicant,self.program)

    def test_match_reject_none(self):
        self.program._reset_matching_attributes()
        self.applicant._reset_matching_attributes()

        rejected_applicant = self.algorithm.match_applicant_to_program(self.applicant,self.program)

        self.assertIsNone(rejected_applicant)
        self.assertTrue(self.applicant.match)
        self.assertEqual(self.applicant.assigned_vacancy,self.program)

    def test_match_reject_other_applicant(self):
        self.program._reset_matching_attributes()
        self.applicant._reset_matching_attributes()

        for i in range(self.regular_capacity):
            temp_applicant = get_applicant_by_priority(self,2)
            self.algorithm.match_applicant_to_program(temp_applicant,self.program)
        rejected_applicant = self.algorithm.match_applicant_to_program(self.applicant,self.program)

        self.assertIsInstance(rejected_applicant,Applicant)
        self.assertNotEqual(rejected_applicant,self.applicant)
        self.assertTrue(self.applicant.match)
        self.assertEqual(self.applicant.assigned_vacancy,self.program)


    def test_match_reject_applicant(self):
        self.program._reset_matching_attributes()
        self.applicant._reset_matching_attributes()

        for i in range(self.regular_capacity):
            temp_applicant = get_applicant_by_priority(self,0)
            self.algorithm.match_applicant_to_program(temp_applicant,self.program)
        rejected_applicant = self.algorithm.match_applicant_to_program(self.applicant,self.program)

        self.assertIsInstance(rejected_applicant,Applicant)
        self.assertEqual(rejected_applicant,self.applicant)
        self.assertFalse(self.applicant.match)
        self.assertIsNone(self.applicant.assigned_vacancy)

    def test_match_no_capacity(self):
        self.program._reset_matching_attributes()
        self.applicant._reset_matching_attributes()

        self.program.regular_assignment.modify_capacity(-self.regular_capacity)

        rejected_applicant = self.algorithm.match_applicant_to_program(self.applicant,self.program)

        self.assertIsInstance(rejected_applicant,Applicant)
        self.assertEqual(rejected_applicant,self.applicant)
        self.assertFalse(self.applicant.match)
        self.assertIsNone(self.applicant.assigned_vacancy)


    def test_run(self):
        self.program._reset_matching_attributes()
        self.applicant._reset_matching_attributes()

        applicants = {}
        bad_priority_app = get_applicant_by_priority(self,1)
        applicants[bad_priority_app.id] = bad_priority_app
        for i in range(self.regular_capacity):
            temp_applicant = get_applicant_by_priority(self,0)
            applicants[temp_applicant.id] = temp_applicant

        programs = {(self.program_id,self.quota_id):self.program}

        self.algorithm.run(applicants,programs)

        for key,app in applicants.items():
            self.assertTrue(app.match)
            if app.id==bad_priority_app.id:
                self.assertIsNone(app.assigned_vacancy)
            else:
                self.assertEqual(app.assigned_vacancy,self.program)




def get_applicant_by_priority(Testclass,priority):
    temp_applicant = Applicant(applicant_id = Testclass.fake.uuid4(), 
                                special_assignment = 0,
                                grade_id = Testclass.grade_id,
                                links = [],
                                siblings = [],
                                vpostulation = np.array([Testclass.program_id]),
                                vpostulation_scores = np.array([random.random()]),
                                vinstitution_id = np.array([Testclass.institution_id]),
                                vpriorities = np.array([priority]),
                                vquota_id = np.array([Testclass.quota_id]),
                                vpriority_profile = np.array([Testclass.fake.random_digit()]))
    return temp_applicant


if __name__ == '__main__':
    main()
