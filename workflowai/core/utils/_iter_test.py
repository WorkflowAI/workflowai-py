from workflowai.core.utils._iter import safe_map


class TestSafeMap:
    def test_safe_map_success(self):
        # Test normal mapping without errors
        input_list = [1, 2, 3]
        result = list(safe_map(input_list, lambda x: x * 2))
        assert result == [2, 4, 6]

    def test_safe_map_with_errors(self):
        # Test mapping with some operations that will raise exceptions
        def problematic_function(x: int) -> int:
            if x == 2:
                raise ValueError("Error for number 2")
            return x * 2

        input_list = [1, 2, 3]
        result = list(safe_map(input_list, problematic_function))
        # Should skip the error for 2 and continue processing
        assert result == [2, 6]
