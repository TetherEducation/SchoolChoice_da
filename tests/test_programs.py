from unittest import TestCase, main
from faker import Faker
from schoolchoice_da.entities import Program, Applicant, Applicant_Queue
import random
import numpy as np


class ProgramTests(TestCase):
    """API logic test suite"""

    def setUp(self) -> None:
        self.fake = Faker()
        Faker.seed()
        self.program_id = str(self.fake.uuid4())

        self.grade_id = self.fake.random_int(0,20)
        self.quota_id = self.fake.random_digit()
        self.institution_id = str(self.fake.uuid4())
        self.regular_capacity = self.fake.random_int(0,100)
        self.special_vacancies = {'special_1_vacancies':self.fake.random_int(2,100),\
                                    'special_2_vacancies':0}

        self.program = Program(program_id = self.program_id,
                                grade_id = self.grade_id,
                                quota_id = self.quota_id,
                                institution_id = self.institution_id,
                                regular_capacity = self.regular_capacity,
                                special_vacancies = self.special_vacancies)

        postulation_length = self.fake.random_int(1,10)
        self.app_score = random.random()
        self.app_priority = self.fake.random_digit()
        self.app_profile = self.fake.random_digit()
        self.applicant = Applicant(applicant_id = str(self.fake.uuid4()),
                                    special_assignment = self.fake.random_int(0,2),
                                    grade_id = self.grade_id,
                                    links = [],
                                    siblings = [],
                                    vpostulation = np.array([str(self.fake.uuid4()) for i in range(postulation_length)]+[self.program_id]),
                                    vpostulation_scores = np.array([random.random() for i in range(postulation_length)]+[self.app_score]),
                                    vinstitution_id = np.array(self.fake.random_choices(elements=[str(self.fake.uuid4()) for i in range(postulation_length)],length=postulation_length)+[self.institution_id]),
                                    vpriorities = np.array([self.fake.random_digit() for i in range(postulation_length)]+[self.app_priority]),
                                    vquota_id = np.array([self.fake.random_digit() for i in range(postulation_length)]+[self.quota_id]),
                                    vpriority_profile = np.array([self.fake.random_digit() for i in range(postulation_length)]+[self.app_profile]))

    def test_get_applicant_score_in_program(self):
        score_in_program = self.program.get_applicant_score_in_program(self.applicant)
        self.assertEqual(score_in_program,self.app_priority+self.app_score)

    def test_get_assignment_type_queue(self):
        assignment_type = 0
        queue = self.program.get_assignment_type_queue(assignment_type)

        self.assertIsInstance(queue,Applicant_Queue)
        self.assertEqual(queue.capacity,self.regular_capacity)

        for assignment_type in [1,2]:
            queue = self.program.get_assignment_type_queue(assignment_type)

            self.assertIsInstance(queue,Applicant_Queue)
            self.assertEqual(queue.capacity,self.special_vacancies[f'special_{assignment_type}_vacancies'])

        assignment_type = self.fake.random_int(3,100)

        self.assertRaises(AttributeError,self.program.get_assignment_type_queue,assignment_type)

    def test_transfer_capacity(self):
        capacity = self.fake.random_int(0,100)
        self.program.transfer_capacity(capacity)

        self.assertEqual(self.program.regular_assignment.capacity,self.regular_capacity+capacity)

    def test_reset_matching_attributes(self):
        self.program.tranfer_capacity = True
        self.program.receive_capacity = True
        self.program.over_capacity = True
        self.program.transfer_capacity(self.fake.random_int(0,100))

        self.program._reset_matching_attributes()

        self.assertFalse(self.program.tranfer_capacity)
        self.assertFalse(self.program.receive_capacity)
        self.assertFalse(self.program.over_capacity)
        self.assertEqual(self.program.regular_assignment.capacity,self.regular_capacity)

    def test_get_capacity_to_transfer(self):
        self.program._reset_matching_attributes()

        assignment_type = 1
        queue = self.program.get_assignment_type_queue(assignment_type)


        capacity_to_transfer = self.program.get_capacity_to_transfer(assignment_type)
        self.assertEqual(capacity_to_transfer,self.special_vacancies['special_1_vacancies'])
        self.assertEqual(queue.capacity,0)
        self.program._reset_matching_attributes()


        temp_assign = self.fake.random_int(1,self.special_vacancies['special_1_vacancies']-1)
        for i in range(temp_assign):
            queue.add_applicant_to_program(self.fake.uuid4())
            queue.add_score_to_program(random.random())

        capacity_to_transfer = self.program.get_capacity_to_transfer(assignment_type)
        self.assertEqual(capacity_to_transfer,self.special_vacancies['special_1_vacancies']-temp_assign)
        self.assertEqual(queue.capacity,temp_assign)
        self.program._reset_matching_attributes()


        for i in range(self.special_vacancies['special_1_vacancies']):
            queue.add_applicant_to_program(self.fake.uuid4())
            queue.add_score_to_program(random.random())

        capacity_to_transfer = self.program.get_capacity_to_transfer(assignment_type)
        self.assertEqual(capacity_to_transfer,0)
        self.assertEqual(queue.capacity,self.special_vacancies['special_1_vacancies'])
        self.program._reset_matching_attributes()


        assignment_type = 2
        queue = self.program.get_assignment_type_queue(assignment_type)
        capacity_to_transfer = self.program.get_capacity_to_transfer(assignment_type)
        self.assertEqual(capacity_to_transfer,0)
        self.assertEqual(queue.capacity,0)
        self.program._reset_matching_attributes()


    def test_force_secured_enrollment_match(self):

        assignment_type = self.applicant.special_assignment

        queue = self.program.get_assignment_type_queue(assignment_type)

        self.program._force_secured_enrollment_match(self.applicant)
        self.assertTrue((self.applicant in queue.vassigned_applicants))
        self.assertTrue((self.app_priority+self.app_score in queue.vassigned_scores))



if __name__ == '__main__':
    main()
