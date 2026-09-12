class Solution:
    def inorderTraversal(self, root):
        result = []
        stack = []

        while root or stack:
            while root:
                stack.append(root)
                root = root.left

            root = stack.pop()
            result.append(root.val)

            root = root.right

        return result
