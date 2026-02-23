"""Test pattern samples for different file types."""

CONTROLLER_TEST_SAMPLE = '''\
"""Example: Controller/View test pattern."""
import pytest
from unittest.mock import patch, MagicMock

@pytest.fixture
def client(app):
    return app.test_client()

class TestUserRegistrationEndpoint:
    @patch("app.views.user_service.register_user")
    def test_register_returns_201_on_success(self, mock_register, client):
        mock_register.return_value = {
            "id": 42,
            "email": "alice.johnson@example.com",
            "username": "alice_j",
        }
        response = client.post("/api/users/register", json={
            "email": "alice.johnson@example.com",
            "username": "alice_j",
            "password": "S3cur3P@ssw0rd!",
        })
        assert response.status_code == 201
        data = response.get_json()
        assert data["email"] == "alice.johnson@example.com"
        mock_register.assert_called_once()

    @patch("app.views.user_service.register_user")
    def test_register_returns_400_for_duplicate_email(self, mock_register, client):
        mock_register.side_effect = ValueError("Email already registered")
        response = client.post("/api/users/register", json={
            "email": "existing@example.com",
            "username": "new_user",
            "password": "An0therP@ss!",
        })
        assert response.status_code == 400
        assert "already registered" in response.get_json()["error"]
'''

SERVICE_TEST_SAMPLE = '''\
"""Example: Service layer test pattern."""
import pytest
from unittest.mock import MagicMock, patch
from decimal import Decimal

class TestOrderService:
    @pytest.fixture
    def order_repo(self):
        return MagicMock()

    @pytest.fixture
    def order_service(self, order_repo):
        from app.services.order_service import OrderService
        return OrderService(order_repo=order_repo)

    def test_place_order_calculates_total_with_tax(self, order_service, order_repo):
        items = [
            {"product_id": 101, "name": "Wireless Keyboard", "price": Decimal("49.99"), "quantity": 2},
            {"product_id": 205, "name": "USB-C Hub", "price": Decimal("29.95"), "quantity": 1},
        ]
        order = order_service.place_order(customer_id=7, items=items, tax_rate=Decimal("0.08"))
        expected_subtotal = Decimal("129.93")
        expected_tax = (expected_subtotal * Decimal("0.08")).quantize(Decimal("0.01"))
        assert order.total == expected_subtotal + expected_tax
        order_repo.save.assert_called_once()

    def test_place_order_raises_on_empty_items(self, order_service):
        with pytest.raises(ValueError, match="at least one item"):
            order_service.place_order(customer_id=7, items=[], tax_rate=Decimal("0.08"))
'''

REPOSITORY_TEST_SAMPLE = '''\
"""Example: Repository/Model test pattern."""
import pytest
from unittest.mock import MagicMock

class TestUserRepository:
    @pytest.fixture
    def mock_session(self):
        return MagicMock()

    @pytest.fixture
    def user_repo(self, mock_session):
        from app.repositories.user_repository import UserRepository
        return UserRepository(session=mock_session)

    def test_find_by_email_returns_user(self, user_repo, mock_session):
        expected_user = MagicMock(id=1, email="maria.garcia@example.com", is_active=True)
        mock_session.query.return_value.filter_by.return_value.first.return_value = expected_user
        result = user_repo.find_by_email("maria.garcia@example.com")
        assert result.email == "maria.garcia@example.com"

    def test_find_by_email_returns_none_when_not_found(self, user_repo, mock_session):
        mock_session.query.return_value.filter_by.return_value.first.return_value = None
        result = user_repo.find_by_email("nobody@example.com")
        assert result is None
'''

FILE_IO_TEST_SAMPLE = '''\
"""Example: File I/O test pattern — mock_open usage."""
import pytest
from unittest.mock import mock_open, patch, MagicMock

class TestFileProcessor:
    def test_read_file_with_mock_open(self):
        """CORRECT: Use mock_open(read_data=...) for `with open() as f: f.read()`."""
        file_content = "line1\\nline2\\nline3\\n"
        m = mock_open(read_data=file_content)

        with patch("builtins.open", m):
            from mymodule import process_file
            result = process_file("data.txt")

        m.assert_called_once_with("data.txt", "r")
        assert result == 3  # e.g. line count

    def test_readlines_with_mock_open(self):
        """CORRECT: For readlines(), set return_value on the mock."""
        lines = ["Alice,30\\n", "Bob,25\\n", "Carol,35\\n"]
        m = mock_open(read_data="".join(lines))
        m.return_value.readlines.return_value = lines

        with patch("builtins.open", m):
            from mymodule import parse_csv
            result = parse_csv("people.csv")

        assert len(result) == 3
        assert result[0]["name"] == "Alice"

    def test_write_file_with_mock_open(self):
        """CORRECT: Verify what was written using call_args."""
        m = mock_open()

        with patch("builtins.open", m):
            from mymodule import save_report
            save_report("output.txt", ["item1", "item2"])

        m.assert_called_once_with("output.txt", "w")
        written = m().write.call_args[0][0]
        assert "item1" in written
        assert "item2" in written

    def test_function_that_reads_and_writes(self):
        """CORRECT: When a function does read + write, mock both calls."""
        input_content = "unsorted\\ndata\\nhere\\n"
        m = mock_open(read_data=input_content)

        with patch("builtins.open", m):
            from mymodule import sort_file
            sort_file("data.txt")

        # Verify write was called
        written = m().write.call_args[0][0]
        assert written.index("data") < written.index("here")
        assert written.index("here") < written.index("unsorted")

    def test_mock_internal_function_calls(self):
        """CORRECT: When function A calls function B, mock B to isolate A."""
        m = mock_open(read_data="some content\\n")

        # main() calls helper() internally — mock helper to isolate main
        with patch("builtins.open", m), patch("mymodule.helper") as mock_helper:
            from mymodule import main
            main()

        mock_helper.assert_called_once()
'''

ASSERTION_PATTERNS_SAMPLE = '''\
"""Example: Robust assertion patterns — NEVER use exact string matching for complex output."""
import pytest

class TestRobustAssertions:
    def test_order_of_elements(self):
        """CORRECT: Test relative order, not exact strings."""
        result = sort_items(["Zebra", "Alpha", "Middle"])
        assert result.index("Alpha") < result.index("Middle")
        assert result.index("Middle") < result.index("Zebra")

    def test_contains_check(self):
        """CORRECT: Check membership, not exact match."""
        result = generate_report(user_id=42)
        assert "User #42" in result
        assert "Total:" in result

    def test_structural_properties(self):
        """CORRECT: Test properties when exact values are unknown."""
        coefficients = compute_filter(freq=1000, rate=48000)
        assert len(coefficients) == 6
        assert all(isinstance(c, float) for c in coefficients)
        assert coefficients[0] == 1.0  # first a_coeff is always 1.0

    def test_type_and_shape(self):
        """CORRECT: Test return type and shape."""
        result = build_matrix(rows=3, cols=4)
        assert isinstance(result, list)
        assert len(result) == 3
        assert all(len(row) == 4 for row in result)

    def test_exception_message(self):
        """CORRECT: Use pytest.raises with match."""
        with pytest.raises(ValueError, match="cannot be negative"):
            withdraw(amount=-100)

    def test_mock_was_called_correctly(self):
        """CORRECT: Verify mock interactions."""
        mock_db.save.assert_called_once()
        call_args = mock_db.save.call_args[0][0]
        assert call_args["email"] == "alice@example.com"
        assert "password" not in call_args  # should not persist raw password
'''

SAMPLES_BY_TYPE = {
    "controller": CONTROLLER_TEST_SAMPLE,
    "service": SERVICE_TEST_SAMPLE,
    "repository": REPOSITORY_TEST_SAMPLE,
    "file_io": FILE_IO_TEST_SAMPLE,
    "assertions": ASSERTION_PATTERNS_SAMPLE,
}
