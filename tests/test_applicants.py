from unittest import TestCase, main
from faker import Faker
from schoolchoice_da.entities import Applicant
import random
import numpy as np


class ApplicantTests(TestCase):
    """API logic test suite"""

    def setUp(self) -> None:
        self.fake = Faker()
        Faker.seed()
        self.applicant_id = str(self.fake.uuid4())
        self.special_assignment = self.fake.random_digit()
        self.grade_id = self.fake.random_int(0,20)
        self.links = np.array([str(self.fake.uuid4()) for i in range(self.fake.random_int(0,4))])
        self.siblings = np.array([str(self.fake.uuid4()) for i in range(self.fake.random_int(0,4))])
        self.postulation_length = self.fake.random_int(1,10)
        self.vpostulation = np.array([str(self.fake.uuid4()) for i in range(self.postulation_length)])
        self.vpostulation_scores = np.array([random.random() for i in range(self.postulation_length)])
        self.vinstitution_id = np.array(self.fake.random_choices(elements=[str(self.fake.uuid4()) for i in range(self.postulation_length)],length=self.postulation_length))
        self.vpriorities = np.array([self.fake.random_digit() for i in range(self.postulation_length)])
        self.vquota_id = np.array([self.fake.random_digit() for i in range(self.postulation_length)])
        self.vpriority_profile = np.array([self.fake.random_digit() for i in range(self.postulation_length)])
        se_pick = self.fake.random_int(0,self.postulation_length-1)
        self.se_program_id = self.fake.boolean()*self.vpostulation[se_pick]
        self.se_quota_id = self.fake.boolean()*self.vquota_id[se_pick]

        self.applicant = Applicant(applicant_id = self.applicant_id,
                                    special_assignment = self.special_assignment,
                                    grade_id = self.grade_id,
                                    links = self.links,
                                    siblings = self.siblings,
                                    vpostulation = self.vpostulation,
                                    vpostulation_scores = self.vpostulation_scores,
                                    vinstitution_id = self.vinstitution_id,
                                    vpriorities = self.vpriorities,
                                    vquota_id = self.vquota_id,
                                    vpriority_profile = self.vpriority_profile,
                                    se_program_id = self.se_program_id,
                                    se_quota_id = self.se_quota_id)

    def test_init_(self):
        self.assertIsInstance(self.applicant.vpostulation_scores,dict)
        self.assertIsInstance(self.applicant.vpriorities,dict)
        self.assertIsInstance(self.applicant.vpriority_profile,dict)

        applicant = Applicant(applicant_id = self.applicant_id,
                                special_assignment = self.special_assignment,
                                grade_id = self.grade_id,
                                links = self.links,
                                siblings = self.siblings,
                                vpostulation = float('nan'),
                                vpostulation_scores = float('nan'),
                                vinstitution_id = float('nan'),
                                vpriorities = float('nan'),
                                vquota_id = float('nan'),
                                vpriority_profile = float('nan'))

        self.assertIsInstance(applicant.vpostulation_scores,dict)
        self.assertIsInstance(applicant.vpriorities,dict)
        self.assertIsInstance(applicant.vpriority_profile,dict)

        self.assertTrue(applicant.match)

    def test_reasign_priority_profile(self):
        index = self.fake.random_int(0,self.postulation_length-1)
        rand_profile = self.fake.random_digit()
        rand_priority = self.fake.random_digit()
        transition = {'priority_profile_sibling_transition':{self.vpriority_profile[index]:rand_profile},\
                    'priority_q{}'.format(self.vquota_id[index]): {rand_profile:rand_priority} }

        program_id = self.applicant.vpostulation[index]
        quota_id = self.applicant.vquota_id[index]

        self.applicant.reasign_priority_profile(index,transition)
        self.assertEqual(self.applicant.vpriority_profile[program_id], rand_profile)
        self.assertEqual(self.applicant.vpriorities[(program_id,quota_id)], rand_priority)

    def test_reorder_postulation(self):
        new_order = list(range(self.postulation_length))
        random.shuffle(new_order)
        self.applicant.reorder_postulation([1,2,3], new_order)

        self.assertTrue((self.applicant.vpostulation==[self.vpostulation[i] for i in new_order]).all())
        self.assertTrue((self.applicant.vinstitution_id==[self.vinstitution_id[i] for i in new_order]).all())
        self.assertTrue((self.applicant.vquota_id==[self.vquota_id[i] for i in new_order]).all())

    def test_reset_matching_attributes(self):

        self.applicant._reset_matching_attributes()

        temp_vpriority_profile = self.applicant.vpriority_profile.copy()
        temp_vpriorities = self.applicant.vpriorities.copy()

        self.applicant.option_n = 10
        self.applicant.assigned_vacancy = True
        self.applicant.match = True

        index = self.fake.random_int(0,self.postulation_length-1)
        rand_profile = self.fake.random_digit()
        transition = {'priority_profile_sibling_transition':{self.vpriority_profile[index]:rand_profile},\
                    'priority_q{}'.format(self.vquota_id[index]): {rand_profile:self.fake.random_digit()} }

        self.applicant.reasign_priority_profile(index,transition)

        self.applicant.reorder_postulation([1,2,3], random.sample(list(range(0,self.postulation_length)),self.postulation_length))

        self.applicant._reset_matching_attributes()

        self.assertEqual(self.applicant.option_n,0)
        self.assertIsNone(self.applicant.assigned_vacancy)
        self.assertFalse(self.applicant.match)

        self.assertTrue((self.applicant.vpostulation==self.vpostulation).all())
        self.assertTrue((self.applicant.vinstitution_id==self.vinstitution_id).all())
        self.assertTrue((self.applicant.vquota_id==self.vquota_id).all())
        self.assertEqual(self.applicant.vpriority_profile,temp_vpriority_profile)
        self.assertEqual(self.applicant.vpriorities,temp_vpriorities)





if __name__ == '__main__':
    main()
