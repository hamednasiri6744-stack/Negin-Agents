import unittest

from code_x_agent.routing import complementarity, handoff_to_negin, route_task


class RoutingTests(unittest.TestCase):
    def test_code_x_primary_for_repository_engineering(self):
        result = route_task("refactor python repository code and add unit tests")
        self.assertTrue(result["ok"])
        self.assertEqual(result["mode"], "code_x_primary")
        self.assertEqual(result["primary_agent"], "@Code-X")
        self.assertFalse(result["handoff_required"])

    def test_negin_primary_for_enterprise_operation(self):
        result = route_task("query Varanegar production SQL sales data")
        self.assertEqual(result["mode"], "negin_primary")
        self.assertEqual(result["primary_agent"], "@Negin Agent v4")
        self.assertTrue(result["handoff_required"])

    def test_collaborative_for_mixed_task(self):
        result = route_task("implement backend API for Varanegar database sales workflow")
        self.assertEqual(result["mode"], "collaborative")
        self.assertEqual(result["primary_agent"], "@Negin Agent v4")
        self.assertEqual(result["secondary_agent"], "@Code-X")

    def test_handoff_is_structured_and_offline(self):
        result = handoff_to_negin(
            "inspect n8n workflow",
            requested_capability="n8n.workflow",
        )
        self.assertTrue(result["handoff_required"])
        self.assertEqual(result["target_agent"], "@Negin Agent v4")
        self.assertFalse(result["network_call_performed"])

    def test_contract_preserves_negin_owned_boundaries(self):
        contract = complementarity()
        self.assertIn("production_sql", contract["code_x_forbidden_direct_domains"])

    def test_negin_pakhsh_business_rule_routes_via_negin(self):
        result = route_task("implement pricing code for Negin Pakhsh business rule")
        self.assertEqual(result["mode"], "collaborative")
        self.assertEqual(result["primary_agent"], "@Negin Agent v4")
        self.assertTrue(result["handoff_required"])

    def test_contract_exposes_semantic_authority(self):
        contract = complementarity()
        self.assertEqual(contract["semantic_authority"]["name"], "NEGIN_PAKHSH_SEMANTIC_CORE")
        self.assertEqual(contract["semantic_authority"]["owner"], "@Negin Agent v4")

    def test_generic_coding_stays_code_x_primary(self):
        result = route_task("refactor python parser and add unit tests")
        self.assertEqual(result["mode"], "code_x_primary")
        self.assertEqual(result["primary_agent"], "@Code-X")


if __name__ == "__main__":
    unittest.main()
