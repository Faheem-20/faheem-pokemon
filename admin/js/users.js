// JavaScript for Pokemon Nexus User Management Dashboard

const API_BASE_URL = "http://127.0.0.1:5000/api";

// 1. JWT Authentication & Role Guard Check
function checkAuth() {
  const token = localStorage.getItem("pokemonNexusAccess") || localStorage.getItem("pokemonNexusToken");
  const userJson = localStorage.getItem("pokemonNexusUser");
  
  if (!token || !userJson) {
    alert("Access Denied: Please log in first.");
    window.location.href = "../index.html";
    return null;
  }

  try {
    const user = JSON.parse(userJson);
    if (user.role !== "admin" && !user.isAdmin) {
      alert("Access Denied: Admin privileges required to access this dashboard.");
      window.location.href = "../index.html";
      return null;
    }
    return token;
  } catch (e) {
    alert("Authentication Error: Invalid session data.");
    window.location.href = "../index.html";
    return null;
  }
}

const token = checkAuth();

// 2. State Variables
let usersData = [];
let filteredData = [];
let searchQuery = "";
let sortBy = "id";
let sortOrder = "asc"; // "asc" or "desc"
let currentPage = 1;
const itemsPerPage = 8;
let deleteTargetId = null;

// DOM Elements
const tableBody = document.getElementById("tableBody");
const searchInput = document.getElementById("searchInput");
const totalUsersCountEl = document.getElementById("totalUsersCount");
const loadingSpinner = document.getElementById("loadingSpinner");
const emptyState = document.getElementById("emptyState");
const usersTable = document.getElementById("usersTable");
const paginationSection = document.getElementById("paginationSection");
const paginationInfo = document.getElementById("paginationInfo");
const prevPageBtn = document.getElementById("prevPageBtn");
const nextPageBtn = document.getElementById("nextPageBtn");
const refreshBtn = document.getElementById("refreshBtn");
const editForm = document.getElementById("editForm");
const confirmDeleteBtn = document.getElementById("confirmDeleteBtn");
const logoutBtn = document.getElementById("logoutBtn");

// 3. API Communication Functions
async function apiRequest(endpoint, method = "GET", body = null) {
  if (!token) return null;
  
  const headers = {
    "Authorization": `Bearer ${token}`,
    "Content-Type": "application/json"
  };

  const config = { method, headers };
  if (body) {
    config.body = JSON.stringify(body);
  }

  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, config);
    if (response.status === 204) return true; // No Content (Delete)
    
    const result = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(result.detail || result.message || "API request failed");
    }
    return result;
  } catch (error) {
    console.error(`Error with API request [${method} ${endpoint}]:`, error);
    alert(`Error: ${error.message}`);
    throw error;
  }
}

// Fetch Users List
async function fetchUsers() {
  showLoading(true);
  try {
    const data = await apiRequest("/auth/users/");
    if (data) {
      usersData = data;
      applyFilters();
    }
  } catch (error) {
    tableBody.innerHTML = `<tr><td colspan="8" style="text-align: center; color: #ff4757; padding: 2rem;">Failed to load user records. Check connection.</td></tr>`;
    showLoading(false);
  }
}

// 4. Data Processing (Filtering, Sorting, Pagination)
function applyFilters() {
  // Search filter
  filteredData = usersData.filter(user => {
    const term = searchQuery.toLowerCase();
    const username = (user.username || "").toLowerCase();
    const email = (user.email || "").toLowerCase();
    const trainerName = (user.trainerName || "").toLowerCase();
    return username.includes(term) || email.includes(term) || trainerName.includes(term);
  });

  // Sorting
  filteredData.sort((a, b) => {
    let valA = a[sortBy];
    let valB = b[sortBy];

    // Handle null values
    if (valA === null || valA === undefined) valA = "";
    if (valB === null || valB === undefined) valB = "";

    // Convert string inputs to lowercase for comparison
    if (typeof valA === "string") valA = valA.toLowerCase();
    if (typeof valB === "string") valB = valB.toLowerCase();

    if (valA < valB) return sortOrder === "asc" ? -1 : 1;
    if (valA > valB) return sortOrder === "asc" ? 1 : -1;
    return 0;
  });

  // Update total counts
  totalUsersCountEl.textContent = usersData.length;

  currentPage = 1; // reset page to 1
  renderTable();
}

function renderTable() {
  showLoading(false);
  tableBody.innerHTML = "";

  if (filteredData.length === 0) {
    emptyState.style.display = "block";
    usersTable.style.display = "none";
    paginationSection.style.display = "none";
    return;
  }

  emptyState.style.display = "none";
  usersTable.style.display = "table";
  paginationSection.style.display = "flex";

  // Calculate pagination boundaries
  const totalItems = filteredData.length;
  const totalPages = Math.ceil(totalItems / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = Math.min(startIndex + itemsPerPage, totalItems);

  // Update pagination UI details
  paginationInfo.textContent = `Showing ${startIndex + 1} to ${endIndex} of ${totalItems} entries`;
  prevPageBtn.disabled = currentPage === 1;
  nextPageBtn.disabled = currentPage === totalPages;

  // Slice items for current page
  const pageItems = filteredData.slice(startIndex, endIndex);

  // Generate rows
  pageItems.forEach(user => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${user.id}</td>
      <td class="highlight" style="font-weight: 600;">${user.username}</td>
      <td>${user.email}</td>
      <td><span class="badge badge-${(user.role || "player").toLowerCase()}">${user.role}</span></td>
      <td>${formatDate(user.date_joined)}</td>
      <td>${formatDate(user.last_login)}</td>
      <td>
        <span class="status-indicator status-${user.is_active ? 'active' : 'inactive'}">
          <span class="status-dot"></span>
          ${user.is_active ? 'Active' : 'Inactive'}
        </span>
      </td>
      <td>
        <div class="action-btn-group">
          <button class="btn-action" title="View details" onclick="viewUserDetails(${user.id})">👁️</button>
          <button class="btn-action" title="Edit user" onclick="openEditForm(${user.id})">✏️</button>
          <button class="btn-action btn-status-toggle" title="${user.is_active ? 'Deactivate' : 'Activate'}" onclick="toggleStatus(${user.id}, ${user.is_active})">
            ${user.is_active ? '❌' : '✅'}
          </button>
          <button class="btn-action btn-delete" title="Delete account" onclick="confirmDelete(${user.id}, '${user.username}')">🗑️</button>
        </div>
      </td>
    `;
    tableBody.appendChild(tr);
  });
}

// 5. Action Modal Functions
window.openModal = function(id) {
  document.getElementById(id).classList.add("show");
};

window.closeModal = function(id) {
  document.getElementById(id).classList.remove("show");
};

// View Details
window.viewUserDetails = function(id) {
  const user = usersData.find(u => u.id === id);
  if (!user) return;

  document.getElementById("viewId").textContent = user.id;
  document.getElementById("viewUsername").textContent = user.username;
  document.getElementById("viewEmail").textContent = user.email;
  document.getElementById("viewRole").textContent = user.role.toUpperCase();
  document.getElementById("viewTrainerName").textContent = user.trainerName || "-";
  document.getElementById("viewLevel").textContent = user.level || 1;
  document.getElementById("viewXp").textContent = user.xp || 0;
  document.getElementById("viewCoins").textContent = user.coins || 0;
  document.getElementById("viewDateJoined").textContent = formatDate(user.date_joined, true);
  document.getElementById("viewLastLogin").textContent = formatDate(user.last_login, true);
  
  const statusHtml = user.is_active 
    ? '<span class="status-indicator status-active"><span class="status-dot"></span>Active</span>'
    : '<span class="status-indicator status-inactive"><span class="status-dot"></span>Inactive</span>';
  document.getElementById("viewStatus").innerHTML = statusHtml;

  openModal("viewModal");
};

// Open Edit Profile Modal
window.openEditForm = function(id) {
  const user = usersData.find(u => u.id === id);
  if (!user) return;

  document.getElementById("editUserId").value = user.id;
  document.getElementById("editUsername").value = user.username;
  document.getElementById("editEmail").value = user.email;
  document.getElementById("editRole").value = user.role;
  document.getElementById("editTrainerName").value = user.trainerName || "";
  document.getElementById("editLevel").value = user.level || 1;
  document.getElementById("editCoins").value = user.coins || 0;
  document.getElementById("editStatus").checked = user.is_active;

  openModal("editModal");
};

// Submit Edit Profile Form
editForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const id = parseInt(document.getElementById("editUserId").value);
  const username = document.getElementById("editUsername").value.trim();
  const email = document.getElementById("editEmail").value.trim();
  const role = document.getElementById("editRole").value;
  const trainer_name = document.getElementById("editTrainerName").value.trim();
  const level = parseInt(document.getElementById("editLevel").value);
  const coins = parseInt(document.getElementById("editCoins").value);
  const is_active = document.getElementById("editStatus").checked;

  try {
    const result = await apiRequest(`/auth/users/${id}/`, "PUT", {
      username,
      email,
      role,
      trainerName: trainer_name,
      level,
      coins,
      is_active
    });

    if (result) {
      // Update local array
      const idx = usersData.findIndex(u => u.id === id);
      if (idx !== -1) {
        usersData[idx] = result;
      }
      closeModal("editModal");
      applyFilters();
    }
  } catch (err) {
    // Error is already alerted inside apiRequest
  }
});

// Toggle Status (Quick action)
window.toggleStatus = async function(id, currentStatus) {
  const newStatus = !currentStatus;
  try {
    const result = await apiRequest(`/auth/users/${id}/`, "PATCH", {
      is_active: newStatus
    });
    if (result) {
      const idx = usersData.findIndex(u => u.id === id);
      if (idx !== -1) {
        usersData[idx].is_active = newStatus;
      }
      applyFilters();
    }
  } catch (err) {}
};

// Delete User Modal
window.confirmDelete = function(id, username) {
  deleteTargetId = id;
  document.getElementById("deleteTargetUsername").textContent = username;
  openModal("deleteModal");
};

// Confirm Delete Account
confirmDeleteBtn.addEventListener("click", async () => {
  if (!deleteTargetId) return;

  try {
    const success = await apiRequest(`/auth/users/${deleteTargetId}/`, "DELETE");
    if (success) {
      usersData = usersData.filter(u => u.id !== deleteTargetId);
      closeModal("deleteModal");
      applyFilters();
    }
  } catch (err) {}
});

// 6. Utility Helper Functions
function showLoading(show) {
  loadingSpinner.style.display = show ? "flex" : "none";
  if (show) {
    usersTable.style.display = "none";
    paginationSection.style.display = "none";
    emptyState.style.display = "none";
  }
}

function formatDate(dateString, includeTime = false) {
  if (!dateString) return "Never";
  try {
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return "Never";
    
    const options = { year: 'numeric', month: 'short', day: 'numeric' };
    if (includeTime) {
      options.hour = '2-digit';
      options.minute = '2-digit';
    }
    return date.toLocaleDateString('en-US', options);
  } catch (e) {
    return "Never";
  }
}

// 7. Event Listeners Initialization
searchInput.addEventListener("input", (e) => {
  searchQuery = e.target.value.trim();
  applyFilters();
});

// Pagination Nav click triggers
prevPageBtn.addEventListener("click", () => {
  if (currentPage > 1) {
    currentPage--;
    renderTable();
  }
});

nextPageBtn.addEventListener("click", () => {
  const totalPages = Math.ceil(filteredData.length / itemsPerPage);
  if (currentPage < totalPages) {
    currentPage++;
    renderTable();
  }
});

// Table Headers Sort Listeners
document.querySelectorAll(".data-table th[data-sort]").forEach(th => {
  th.addEventListener("click", () => {
    const field = th.getAttribute("data-sort");
    
    // Toggle sort order or field
    if (sortBy === field) {
      sortOrder = sortOrder === "asc" ? "desc" : "asc";
    } else {
      sortBy = field;
      sortOrder = "asc";
    }

    // Set classes for sorting icons
    document.querySelectorAll(".data-table th").forEach(header => {
      header.classList.remove("sort-asc", "sort-desc");
    });
    th.classList.add(sortOrder === "asc" ? "sort-asc" : "sort-desc");

    applyFilters();
  });
});

// Refresh button trigger
refreshBtn.addEventListener("click", () => {
  fetchUsers();
});

// Logout listener
logoutBtn.addEventListener("click", (e) => {
  e.preventDefault();
  localStorage.removeItem("pokemonNexusAccess");
  localStorage.removeItem("pokemonNexusRefresh");
  localStorage.removeItem("pokemonNexusToken");
  localStorage.removeItem("pokemonNexusUser");
  window.location.href = "../index.html";
});

// Initialize on page load
if (token) {
  fetchUsers();
}
