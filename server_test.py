import unittest

from server import app


class test_index_user_hrefs_use_user_id(unittest.TestCase):
    def test_index_user_hrefs_use_user_id(self):
        response = app.test_client().get('/')
        self.assertTrue(str(response.data).__contains__(
            'href="/user_path_id/8457418831985727/'))  # example user path id that should be in html

    def test_access_denies_when_manually_accessing_a_users_page(self):
        response = app.test_client().get('/aking/')
        self.assertTrue(str(response.data).__contains__('Access Denied'))

    # trying to page can be accessed when logged in here but struggling
    # def test_no_access_denies_when_manually_accessing_a_users_page_when_logged_in(self):
    #     with app.test_client() as c:
    #         with c.session_transaction() as session:
    #             session['userid'] = '5173398951656916'
    #             session['username'] = 'aking'
    #             session['token'] = str(os.urandom(16))
    #     response = app.test_client().get('/aking/')
    #     print(response.data)
    #     # self.assertFalse(str(response.data).__contains__('Access Denied'))

    def test_login_fail_when_username_and_password_are_wrong(self):
        data = dict()
        data['username'] = 'nonsense'
        data['password'] = 'nonsense'
        response = app.test_client().post('/login/', data=data, follow_redirects=True)
        self.assertTrue(str(response.data).__contains__('Username or password incorrect'))

    def test_login_fail_when_password_is_wrong(self):
        data = dict()
        data['username'] = 'aking'
        data['password'] = 'nonsense'
        response = app.test_client().post('/login/', data=data, follow_redirects=True)
        self.assertTrue(str(response.data).__contains__('Username or password incorrect'))

    def test_password_rest_for_email_that_exists(self):
        data = dict()
        data['email'] = 'a.king@email.com'
        response = app.test_client().post('/reset/', data=data, follow_redirects=True)
        self.assertTrue(
            str(response.data).__contains__('If email exists, a reset link will be sent to a.king@email.com'))

    def test_password_rest_for_email_that_does_not_exists(self):
        data = dict()
        data['email'] = 'nonsense@email.com'
        response = app.test_client().post('/reset/', data=data, follow_redirects=True)
        self.assertTrue(
            str(response.data).__contains__('If email exists, a reset link will be sent to nonsense@email.com'))
