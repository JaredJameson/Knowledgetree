# Category Management System - Testing Checklist

## 🎯 Testing Session: 2026-01-20

### ✅ Implementation Status
- **Phase 3A (Backend)**: 27/27 integration tests passing ✅
- **Phase 3B (Frontend)**: All components implemented ✅
- **Development Servers**: Both running ✅

### 🧪 User Testing Checklist

#### 1. Basic CRUD Operations
- [ ] **Create Root Category**
  - Open Projects page → Click "Categories" button
  - Click "Create Root Category"
  - Fill in: Name, Description (optional), Color
  - Verify category appears in tree

- [ ] **Create Subcategory**
  - Hover over existing category
  - Click "+" (Add) button
  - Fill in details
  - Verify subcategory appears under parent with indentation

- [ ] **Edit Category**
  - Hover over category
  - Click "✏️" (Edit) button
  - Modify name, description, color
  - Verify changes are saved and displayed

- [ ] **Delete Category**
  - Hover over category
  - Click "🗑️" (Delete) button
  - Test cascade delete (delete parent with children)
  - Test non-cascade delete (should fail if has children)

#### 2. Tree Interaction
- [ ] **Expand/Collapse**
  - Click chevron icon to expand category
  - Verify children are displayed
  - Click chevron icon to collapse
  - Verify children are hidden

- [ ] **Visual Hierarchy**
  - Verify depth-based indentation (20px per level)
  - Verify folder icons change (open/closed)
  - Verify color coding is applied correctly

#### 3. Edge Cases
- [ ] **Maximum Depth**
  - Try creating categories beyond depth 10
  - Verify appropriate error handling

- [ ] **Empty States**
  - New project with no categories
  - Verify "No categories" message appears
  - Verify "Create Root Category" CTA is visible

- [ ] **Long Names**
  - Create category with very long name
  - Verify text wraps or truncates properly

- [ ] **Special Characters**
  - Create category with special characters in name
  - Verify proper handling and display

#### 4. Color Picker
- [ ] **Preset Colors**
  - Test all 8 preset colors
  - Verify visual preview updates

- [ ] **Custom Color**
  - Use HTML color picker for custom color
  - Verify custom color is saved and displayed

#### 5. Performance Testing
- [ ] **Large Tree**
  - Create 100+ categories (can use API script)
  - Verify tree renders without lag
  - Test expand/collapse performance

- [ ] **Concurrent Operations**
  - Open multiple category dialogs
  - Verify no state conflicts

#### 6. API Endpoint Verification

**Base URL**: `http://localhost:8765/api/v1`

- [ ] `GET /categories?project_id={id}` - List categories
- [ ] `GET /categories/tree/{project_id}` - Get category tree
- [ ] `GET /categories/{id}` - Get single category
- [ ] `POST /categories?project_id={id}` - Create category
- [ ] `PATCH /categories/{id}` - Update category
- [ ] `DELETE /categories/{id}?cascade=true` - Delete with cascade
- [ ] `DELETE /categories/{id}?cascade=false` - Delete without cascade
- [ ] `GET /categories/{id}/children` - Get direct children

#### 7. Error Handling
- [ ] **Validation Errors**
  - Try creating category with empty name
  - Try creating category with invalid parent_id
  - Verify error messages are user-friendly

- [ ] **Network Errors**
  - Simulate network failure (stop backend)
  - Verify appropriate error messages
  - Verify graceful degradation

#### 8. Internationalization (i18n)
- [ ] **Polish Language**
  - Verify all UI text is in Polish
  - Verify translations are correct

- [ ] **English Language**
  - Switch to English
  - Verify all UI text is in English
  - Verify translations are correct

### 🐛 Bugs Found
*(Document any issues discovered during testing)*

---

### 📊 Test Results Summary
- **Total Tests**: 0 / 40
- **Passed**: 0
- **Failed**: 0
- **Blocked**: 0

### 🎯 Next Actions
Based on testing results, prioritize:
1. Critical bug fixes
2. UX improvements
3. Performance optimizations
4. Documentation updates
