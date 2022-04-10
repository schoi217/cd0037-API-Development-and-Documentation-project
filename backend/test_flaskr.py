import os
import unittest
import json
from flask_sqlalchemy import SQLAlchemy

from flaskr import create_app
from models import setup_db, Question, Category


class TriviaTestCase(unittest.TestCase):
    """This class represents the trivia test case"""

    def setUp(self):
        """Define test variables and initialize app."""
        self.app = create_app()
        self.client = self.app.test_client
        self.database_name = "trivia_test"
        self.database_path = "postgres://{}/{}".format('localhost:5432', self.database_name)
        setup_db(self.app, self.database_path)

        self.new_question = {
            'question': 'test question',
            'answer': 'test answer',
            'category': '3',
            'difficulty': '5'
        }

        # binds the app to the current context
        with self.app.app_context():
            self.db = SQLAlchemy()
            self.db.init_app(self.app)
            # create all tables
            self.db.create_all()

    def tearDown(self):
        """Executed after reach test"""
        pass


    def test_get_categories(self):
        res = self.client().get("/categories")
        data = json.loads(res.data)
        #make sure status is a success
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        #ensure there is a return for categories and total categories
        self.assertTrue(data['categories'])
        self.assertTrue(data['totalCategories'])

    def test_fail_categories(self):
        #delete category
        Category.query.delete()
        res = self.client().get("/categories")
        data = json.loads(res.data)
        #fail because there is no category
        self.assertEqual(res.status_code, 404)
        self.assertEqual(data["success"], False)
        self.assertEqual(data["message"], "resource not found")


    def test_get_questions(self):
        res = self.client().get('/questions')
        data = json.loads(res.data)

        #success in questions
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        #ensure there is a reutn in total questions, categories, and current cat
        self.assertTrue(data['total_questions'], True)
        self.assertTrue(data['current_category'])
        self.assertTrue(data['categories'])

    def test_404_request_past_valid_page(self):
        res = self.client().get("/books?page=1000")
        data = json.loads(res.data)
        #ensure pagination on page past available pages fails
        self.assertEqual(res.status_code, 404)
        self.assertEqual(data["success"], False)
        self.assertEqual(data["message"], "resource not found")


    def test_delete_questions(self):
        res = self.client().delete('/questions/9')
        data = json.loads(res.data)

        question = Question.query.filter(Question.id==9).one_or_none()
        #success in deleting question
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertEqual(data['deleted'], 9)


    def test_delete_question_that_doesnt_exist(self):
        res = self.client().delete('/questions/1000')
        data = json.loads(res.data)

        question = Question.query.filter(Question.id==1000).one_or_none()
        #ensure a question that doesn't exist can not be deleted
        self.assertEqual(res.status_code, 422)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'unprocessable')


    def test_add_question(self):
        res = self.client().post('/questions', json=self.new_question)
        data = json.loads(res.data)
        #successfully create a new question
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(data['created'])

    def test_add_question_fail(self):
        #load a failing json body
        res = self.client().post('/questions', json={'fail':'fail'})
        data = json.loads(res.data)
        #make sure it fails
        self.assertFalse(data['success'])
        #right error code and message
        self.assertEqual(data['error'], 422)
        self.assertEqual(res.status_code, 422)
        self.assertEqual(data['message'], 'unprocessable')

    def test_search_questions(self):
        #send post request with body
        res = self.client().post('/questions', json={'searchTerm': 'van'})
        data = json.loads(res.data)
        # proper success code
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertEqual(len(data['questions']), 1)
        self.assertEqual(data['questions'][0]['id'], 18)

    def test_search_questions_fail(self):
        res = self.client().post('/questions',
                                      json={'searchTerm': 'abcdefghijk'})
        data = json.loads(res.data)
        #right error code and message
        self.assertEqual(res.status_code, 404)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'resource not found')

    def test_get_quiz(self):
        res = self.client().post('/quizzes',
                                json={'previous_questions': [10,40],
                                      'quiz_category': {'type': 'Art',
                                                        'id': '2'}
                                      })
        # send post request with data from body
        data = json.loads(res.data)
        #proper status code and success
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        #make sure the question is from the right category
        self.assertEqual(data['question']['category'], 2)
        #make sure the question is not the id from previous questions
        self.assertNotEqual(data['question']['id'], 10)
        self.assertNotEqual(data['question']['id'], 40)

    def test_play_quiz_fails(self):
        """Tests playing quiz game failure 400"""

        #send post request with no body
        response = self.client().post('/quizzes', json={})
        data = json.loads(response.data)

        #right error code and message
        self.assertEqual(response.status_code, 400)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'bad request')




# Make the tests conveniently executable
if __name__ == "__main__":
    unittest.main()
