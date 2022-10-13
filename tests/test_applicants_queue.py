from unittest import TestCase, main
from faker import Faker
from schoolchoice_da.entities import Applicant_Queue


class ApplicantQueueTests(TestCase):
    """API logic test suite"""

    def setUp(self) -> None:
        self.fake = Faker()
        Faker.seed()
        self.capacity = self.fake.random_int(0,100)

        self.queue_obj = Applicant_Queue(self.capacity)
        self.queue_obj.reset_assignment()


    def test_add_applicant(self):
        applicant_id = str(self.fake.uuid4())
        self.queue_obj.add_applicant_to_program(applicant_id)

        self.assertTrue((applicant_id in self.queue_obj.vassigned_applicants))


    def test_add_score(self):
        score = self.fake.random_int()
        self.queue_obj.add_score_to_program(score)

        self.assertTrue((score in self.queue_obj.vassigned_scores))


    def test_modify_capacity(self):
        capacity = self.fake.random_int(1,100)
        self.queue_obj.modify_capacity(capacity)

        self.assertEqual(self.queue_obj.capacity,self.capacity+capacity)

        self.queue_obj.modify_capacity(-capacity)

        self.assertEqual(self.queue_obj.capacity,self.capacity)


    def test_reset_assignment(self):
        self.queue_obj.add_applicant_to_program(str(self.fake.uuid4()))
        self.queue_obj.add_score_to_program(self.fake.random_int())
        self.queue_obj.modify_capacity(self.fake.random_int(1,100))
        self.queue_obj.reset_assignment()

        self.assertEqual(len(self.queue_obj.vassigned_applicants),0)
        self.assertEqual(len(self.queue_obj.vassigned_scores),0)
        self.assertEqual(self.queue_obj.capacity,self.capacity)


    def test_check_capacity_contraints(self):
        self.queue_obj.reset_assignment()

        if self.capacity==0:
            self.queue_obj.modify_capacity(1)

        self.assertFalse(self.queue_obj.check_capacity_contraints())

        for i in range(self.capacity+1):
            self.queue_obj.add_applicant_to_program(str(self.fake.uuid4()))

        self.assertTrue(self.queue_obj.check_capacity_contraints())


    def test_get_cut_off_score(self):
        queue = Applicant_Queue(0)
        queue.reset_assignment()
        self.assertEqual(queue.get_cut_off_score(),float('inf'))

        queue.modify_capacity(1)
        self.assertEqual(queue.get_cut_off_score(),0)

        score_1 = self.fake.random_int()
        score_2 = self.fake.random_int()
        queue.add_applicant_to_program(str(self.fake.uuid4()))
        queue.add_applicant_to_program(str(self.fake.uuid4()))
        queue.add_score_to_program(score_1)
        queue.add_score_to_program(score_2)
        self.assertEqual(queue.get_cut_off_score(),max(score_1,score_2))


    def test_get_cut_off_applicant(self):
        self.queue_obj.reset_assignment()

        for i in range(self.capacity):
            self.queue_obj.add_applicant_to_program(str(self.fake.uuid4()))
            self.queue_obj.add_score_to_program(self.fake.random_int(1,100))

        applicant_id = str(self.fake.uuid4())
        self.queue_obj.add_applicant_to_program(applicant_id)
        self.queue_obj.add_score_to_program(101)

        self.assertEqual(self.queue_obj.get_cut_off_applicant(101),applicant_id)


    def test_reassign_applicants_and_scores(self):
        self.queue_obj.reset_assignment()

        applicant_id = str(self.fake.uuid4())
        score = self.fake.random_int()
        self.queue_obj.add_applicant_to_program(applicant_id)
        self.queue_obj.add_score_to_program(score)

        for i in range(self.fake.random_int(0,self.capacity)):
            self.queue_obj.add_applicant_to_program(str(self.fake.uuid4()))
            self.queue_obj.add_score_to_program(self.fake.random_int())

        new_applicant_id = str(self.fake.uuid4())
        new_score = self.fake.random_int()

        self.queue_obj.reassign_applicants_and_scores(new_applicant_id,new_score,applicant_id)

        self.assertTrue((new_applicant_id in self.queue_obj.vassigned_applicants))
        self.assertTrue((new_score in self.queue_obj.vassigned_scores))

        self.assertFalse((applicant_id in self.queue_obj.vassigned_applicants))
        self.assertFalse((score in self.queue_obj.vassigned_scores))



if __name__ == '__main__':
    main()
