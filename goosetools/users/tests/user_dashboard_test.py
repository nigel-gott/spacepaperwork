from django.urls.base import reverse

from goosetools.tests.goosetools_test_case import GooseToolsTestCase


class UserDashboardTest(GooseToolsTestCase):
    def test_user_without_user_admin_permission_cannot_visit_dashboard(self):
        self.client.force_login(self.other_site_user)
        self.other_user.groupmember_set.all().delete()
        response = self.client.get(reverse("user_dashboard"))
        self.assertEqual(response.status_code, 403)

    def test_user_with_user_admin_permission_can_visit_dashboard(self):
        self.client.force_login(self.other_site_user)
        self.other_user.give_group(self.user_admin_group)
        response = self.client.get(reverse("user_dashboard"))
        self.assertEqual(response.status_code, 200)
