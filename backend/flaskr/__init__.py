import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

def paginate(request, selection):
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [question.format() for question in selection]
    current_questions = questions[start:end]

    return current_questions

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)

    """
    @TODO: Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
    """

    CORS(app, resources={'/': {'origins': '*'}})


    """
    @TODO: Use the after_request decorator to set Access-Control-Allow
    """

    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,true')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response

    """
    @TODO:
    Create an endpoint to handle GET requests
    for all available categories.
    """

    @app.route('/categories', methods=['GET'])
    def get_categories():
        categories = Category.query.order_by(Category.id).all()
        formatted_categories = {}
        for category in categories:
            formatted_categories[category.id] = category.type

        if len(formatted_categories) == 0:
            abort(404)

        else:
            return jsonify({
                'success': True,
                'categories': formatted_categories,
                'totalCategories': len(formatted_categories)
            })

    """
    @TODO:
    Create an endpoint to handle GET requests for questions,
    including pagination (every 10 questions).
    This endpoint should return a list of questions,
    number of total questions, current category, categories.

    TEST: At this point, when you start the application
    you should see questions and categories generated,
    ten questions per page and pagination at the bottom of the screen for three pages.
    Clicking on the page numbers should update the questions.
    """

    @app.route('/questions')
    def get_questions():
        #query all questions and paginate
        selection = Question.query.order_by(Question.category).all()
        current_questions = paginate(request, selection)
        totalQuestions = len(selection)

        #query all categories & make dictionary
        categories = Category.query.order_by(Category.type).all()
        category_dict = {category.id: category.type for category in categories}

        #get current category from first question present
        category_num = current_questions[0]['category']
        category = Category.query.filter(Category.id==category_num).first()
        category_type = category.type

        if len(current_questions) == 0:
            abort(404)

        return jsonify({
            'success': True,
            'questions': current_questions,
            'total_questions': totalQuestions,
            'current_category': category_type,
            'categories': {category.id: category.type for category in categories},
        })


    """
    @TODO:
    Create an endpoint to DELETE question using a question ID.

    TEST: When you click the trash icon next to a question, the question will be removed.
    This removal will persist in the database and when you refresh the page.
    """

    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    def delete_question(question_id):
        try:
            question = Question.query.filter(Question.id==question_id).one_or_none()
            if question is None:
                abort(404)

            question.delete()

            return jsonify({
                'success': True,
                'deleted': question_id
            })

        except:
            abort(422)

    """
    @TODO:
    Create a POST endpoint to get questions based on a search term.
    It should return any questions for whom the search term
    is a substring of the question.

    TEST: Search by any phrase. The questions list will update to include
    only question that include that string within their question.
    Try using the word "title" to start.
    """

    @app.route('/questions', methods=['POST'])
    def search_create_questions():
        form = request.get_json()
        search_term = form.get('searchTerm', False)
        if search_term:
            questions = Question.query.filter(Question.question.ilike('%' + search_term + '%')).all()
            if len(questions) == 0:
                abort(404)
            current_questions = paginate(request, questions)
            categories = {}
            for question in questions:
                category = Category.query.filter(Category.id==question.category).first()
                if category.id not in categories:
                    categories[category.id] = category.type
            category_num = current_questions[0]['category']
            category = Category.query.filter(Category.id==category_num).first()
            category_type = category.type
            return jsonify({
                'success': True,
                'questions': current_questions,
                'total_questions': len(questions),
                'current_category': category_type,
                'categories': categories
            })

        else:
            new_question = form.get('question', None)
            new_answer = form.get('answer', None)
            new_category = str(form.get('category', None))
            new_difficulty = form.get('difficulty', None)

            try:
                new_question = Question(question=new_question, answer=new_answer,
                                        category=new_category,
                                        difficulty=new_difficulty)

                new_question.insert()

                return jsonify({
                    'success': True,
                    'created': new_question.id
                })
            except:
                abort(422)



    """
    @TODO:
    Create a GET endpoint to get questions based on category.

    TEST: In the "List" tab / main screen, clicking on one of the
    categories in the left column will cause only questions of that
    category to be shown.
    """

    @app.route('/categories/<int:category_id>/questions', methods=['GET'])
    def get_questions_by_category(category_id):
        questions = Question.query.filter(Question.category == category_id).all()
        current_questions = paginate(request, questions)
        categories = {}
        for question in questions:
            category = Category.query.filter(Category.id==question.category).first()
            if category.id not in categories:
                categories[category.id] = category.type
        category_num = current_questions[0]['category']
        category = Category.query.filter(Category.id==category_num).first()
        category_type = category.type

        if len(current_questions) == 0:
            abort(404)

        else:
            return jsonify({
                'success': True,
                'questions': current_questions,
                'total_questions': len(questions),
                'current_category': category_type,
                'categories': categories
            })



    """
    @TODO:
    Create a POST endpoint to get questions to play the quiz.
    This endpoint should take category and previous question parameters
    and return a random questions within the given category,
    if provided, and that is not one of the previous questions.

    TEST: In the "Play" tab, after a user selects "All" or a category,
    one question at a time is displayed, the user is allowed to answer
    and shown whether they were correct or not.
    """

    @app.route('/quizzes', methods=['POST'])
    def get_quizzes():
        #get request values of previous questions and quiz category
        previous_questions = request.get_json().get('previous_questions')
        quiz_category = request.get_json().get('quiz_category')

        if previous_questions is None or quiz_category is None:
            return abort(400)

        if quiz_category['id'] == 0:
            questions = Question.query.filter(Question.id.notin_(previous_questions)).all()
        else:
            questions = Question.query.filter(Question.category==quiz_category['id'], Question.id.notin_(previous_questions)).all()

        if questions:
            return jsonify({
                'success': True,
                'question': random.choice(questions).format()
            })



    """
    @TODO:
    Create error handlers for all expected errors
    including 404 and 422.
    """


    @app.errorhandler(404)
    def not_found(error):
        return (
            jsonify({"success": False, "error": 404, "message": "resource not found"}),
            404,
        )

    @app.errorhandler(422)
    def unprocessable(error):
        return (
            jsonify({"success": False, "error": 422, "message": "unprocessable"}),
            422,
        )

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({"success": False, "error": 400, "message": "bad request"}), 400

    @app.errorhandler(405)
    def not_found(error):
        return (
            jsonify({"success": False, "error": 405, "message": "method not allowed"}),
            405,
        )


    return app
