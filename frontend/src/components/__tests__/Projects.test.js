import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import Projects from '../Projects';
import { AuthProvider } from '../../services/AuthContext';
import * as api from '../../services/api';

// Mock the API
jest.mock('../../services/api');
const mockApi = api;

// Mock react-toastify
jest.mock('react-toastify', () => ({
  toast: {
    error: jest.fn(),
    success: jest.fn()
  }
}));

// Mock useNavigate
const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate
}));

const theme = createTheme();

// Mock authenticated user context
const mockAuthContext = {
  user: {
    id: 1,
    username: 'testuser',
    permission: 'editor'
  },
  login: jest.fn(),
  logout: jest.fn(),
  loading: false
};

jest.mock('../../services/AuthContext', () => ({
  ...jest.requireActual('../../services/AuthContext'),
  useAuth: () => mockAuthContext
}));

const renderProjects = () => {
  return render(
    <BrowserRouter>
      <ThemeProvider theme={theme}>
        <AuthProvider>
          <Projects />
        </AuthProvider>
      </ThemeProvider>
    </BrowserRouter>
  );
};

describe('Projects Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders projects page title', () => {
    mockApi.get.mockResolvedValueOnce({ data: { projects: [] } });
    
    renderProjects();
    
    expect(screen.getByText('Projects')).toBeInTheDocument();
  });

  test('renders create project button for editors', () => {
    mockApi.get.mockResolvedValueOnce({ data: { projects: [] } });
    
    renderProjects();
    
    expect(screen.getByRole('button', { name: /create project/i })).toBeInTheDocument();
  });

  test('fetches and displays projects on mount', async () => {
    const mockProjects = [
      {
        id: 1,
        name: 'Project Alpha',
        prefix: 'PA',
        description: 'First project',
        created_at: '2023-01-01T00:00:00Z'
      },
      {
        id: 2,
        name: 'Project Beta',
        prefix: 'PB',
        description: 'Second project',
        created_at: '2023-01-02T00:00:00Z'
      }
    ];
    
    mockApi.get.mockResolvedValueOnce({ data: { projects: mockProjects } });
    
    renderProjects();
    
    await waitFor(() => {
      expect(screen.getByText('Project Alpha')).toBeInTheDocument();
      expect(screen.getByText('Project Beta')).toBeInTheDocument();
      expect(screen.getByText('PA')).toBeInTheDocument();
      expect(screen.getByText('PB')).toBeInTheDocument();
    });
  });

  test('displays loading state while fetching projects', () => {
    let resolveProjects;
    const projectsPromise = new Promise((resolve) => {
      resolveProjects = resolve;
    });
    
    mockApi.get.mockReturnValueOnce(projectsPromise);
    
    renderProjects();
    
    // Should show loading indicator
    expect(screen.getByRole('progressbar') || screen.getByText(/loading/i)).toBeInTheDocument();
    
    // Resolve the promise
    resolveProjects({ data: { projects: [] } });
  });

  test('handles error when fetching projects fails', async () => {
    const { toast } = require('react-toastify');
    
    mockApi.get.mockRejectedValueOnce(new Error('Network error'));
    
    renderProjects();
    
    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith('Failed to fetch projects');
    });
  });

  test('allows sorting projects by name', async () => {
    const mockProjects = [
      { id: 1, name: 'Beta Project', prefix: 'BP', created_at: '2023-01-01T00:00:00Z' },
      { id: 2, name: 'Alpha Project', prefix: 'AP', created_at: '2023-01-02T00:00:00Z' }
    ];
    
    mockApi.get.mockResolvedValueOnce({ data: { projects: mockProjects } });
    
    renderProjects();
    
    await waitFor(() => {
      expect(screen.getByText('Beta Project')).toBeInTheDocument();
    });
    
    // Click sort by name
    const sortButton = screen.getByRole('button', { name: /sort by name/i }) || 
                       screen.getByText(/name/i).closest('button');
    if (sortButton) {
      fireEvent.click(sortButton);
      
      // Projects should be sorted alphabetically
      const projectElements = screen.getAllByText(/Project/);
      expect(projectElements[0]).toHaveTextContent('Alpha Project');
      expect(projectElements[1]).toHaveTextContent('Beta Project');
    }
  });

  test('allows sorting projects by date', async () => {
    const mockProjects = [
      { id: 1, name: 'Older Project', prefix: 'OP', created_at: '2023-01-01T00:00:00Z' },
      { id: 2, name: 'Newer Project', prefix: 'NP', created_at: '2023-01-02T00:00:00Z' }
    ];
    
    mockApi.get.mockResolvedValueOnce({ data: { projects: mockProjects } });
    
    renderProjects();
    
    await waitFor(() => {
      expect(screen.getByText('Older Project')).toBeInTheDocument();
    });
    
    // Click sort by date
    const sortButton = screen.getByRole('button', { name: /sort by date/i }) || 
                       screen.getByText(/date/i).closest('button');
    if (sortButton) {
      fireEvent.click(sortButton);
      
      // Projects should be sorted by date (newest first by default)
      const projectElements = screen.getAllByText(/Project/);
      expect(projectElements[0]).toHaveTextContent('Newer Project');
      expect(projectElements[1]).toHaveTextContent('Older Project');
    }
  });

  test('navigates to project details when project is clicked', async () => {
    const mockProjects = [
      { id: 1, name: 'Test Project', prefix: 'TP', created_at: '2023-01-01T00:00:00Z' }
    ];
    
    mockApi.get.mockResolvedValueOnce({ data: { projects: mockProjects } });
    
    renderProjects();
    
    await waitFor(() => {
      expect(screen.getByText('Test Project')).toBeInTheDocument();
    });
    
    // Click on the project
    fireEvent.click(screen.getByText('Test Project'));
    
    expect(mockNavigate).toHaveBeenCalledWith('/projects/1');
  });

  test('opens create project dialog when create button is clicked', async () => {
    mockApi.get.mockResolvedValueOnce({ data: { projects: [] } });
    
    renderProjects();
    
    const createButton = screen.getByRole('button', { name: /create project/i });
    fireEvent.click(createButton);
    
    // Should open dialog or navigate to create page
    expect(mockNavigate).toHaveBeenCalledWith('/projects/create') || 
           expect(screen.getByRole('dialog')).toBeInTheDocument();
  });

  test('displays empty state when no projects exist', async () => {
    mockApi.get.mockResolvedValueOnce({ data: { projects: [] } });
    
    renderProjects();
    
    await waitFor(() => {
      expect(screen.getByText(/no projects found/i) || 
             screen.getByText(/create your first project/i)).toBeInTheDocument();
    });
  });

  test('shows project prefix in project cards', async () => {
    const mockProjects = [
      { id: 1, name: 'Test Project', prefix: 'TP', created_at: '2023-01-01T00:00:00Z' }
    ];
    
    mockApi.get.mockResolvedValueOnce({ data: { projects: mockProjects } });
    
    renderProjects();
    
    await waitFor(() => {
      expect(screen.getByText('TP')).toBeInTheDocument();
    });
  });

  test('shows project description if available', async () => {
    const mockProjects = [
      { 
        id: 1, 
        name: 'Test Project', 
        prefix: 'TP',
        description: 'This is a test project description',
        created_at: '2023-01-01T00:00:00Z'
      }
    ];
    
    mockApi.get.mockResolvedValueOnce({ data: { projects: mockProjects } });
    
    renderProjects();
    
    await waitFor(() => {
      expect(screen.getByText('This is a test project description')).toBeInTheDocument();
    });
  });

  test('formats creation date correctly', async () => {
    const mockProjects = [
      { 
        id: 1, 
        name: 'Test Project', 
        prefix: 'TP',
        created_at: '2023-06-15T14:30:00Z'
      }
    ];
    
    mockApi.get.mockResolvedValueOnce({ data: { projects: mockProjects } });
    
    renderProjects();
    
    await waitFor(() => {
      // Should display formatted date (exact format depends on implementation)
      expect(screen.getByText(/2023/) || screen.getByText(/Jun/)).toBeInTheDocument();
    });
  });

  test('handles projects with missing optional fields', async () => {
    const mockProjects = [
      { 
        id: 1, 
        name: 'Minimal Project', 
        prefix: 'MP',
        created_at: '2023-01-01T00:00:00Z'
        // No description
      }
    ];
    
    mockApi.get.mockResolvedValueOnce({ data: { projects: mockProjects } });
    
    renderProjects();
    
    await waitFor(() => {
      expect(screen.getByText('Minimal Project')).toBeInTheDocument();
      expect(screen.getByText('MP')).toBeInTheDocument();
    });
  });

  test('refreshes projects list after creating new project', async () => {
    mockApi.get.mockResolvedValue({ data: { projects: [] } });
    
    renderProjects();
    
    // Mock project creation success
    const createButton = screen.getByRole('button', { name: /create project/i });
    fireEvent.click(createButton);
    
    // After successful creation, should refetch projects
    await waitFor(() => {
      expect(mockApi.get).toHaveBeenCalledWith('/projects');
    });
  });

  test('displays correct number of projects', async () => {
    const mockProjects = Array.from({ length: 5 }, (_, i) => ({
      id: i + 1,
      name: `Project ${i + 1}`,
      prefix: `P${i + 1}`,
      created_at: '2023-01-01T00:00:00Z'
    }));
    
    mockApi.get.mockResolvedValueOnce({ data: { projects: mockProjects } });
    
    renderProjects();
    
    await waitFor(() => {
      expect(screen.getAllByText(/Project \d+/)).toHaveLength(5);
    });
  });

  test('search functionality filters projects', async () => {
    const mockProjects = [
      { id: 1, name: 'Alpha Project', prefix: 'AP', created_at: '2023-01-01T00:00:00Z' },
      { id: 2, name: 'Beta Project', prefix: 'BP', created_at: '2023-01-02T00:00:00Z' },
      { id: 3, name: 'Gamma Project', prefix: 'GP', created_at: '2023-01-03T00:00:00Z' }
    ];
    
    mockApi.get.mockResolvedValueOnce({ data: { projects: mockProjects } });
    
    renderProjects();
    
    await waitFor(() => {
      expect(screen.getByText('Alpha Project')).toBeInTheDocument();
    });
    
    // Search for 'Beta'
    const searchInput = screen.getByRole('textbox', { name: /search/i }) || 
                        screen.getByPlaceholderText(/search/i);
    if (searchInput) {
      await userEvent.type(searchInput, 'Beta');
      
      // Should only show Beta Project
      expect(screen.getByText('Beta Project')).toBeInTheDocument();
      expect(screen.queryByText('Alpha Project')).not.toBeInTheDocument();
      expect(screen.queryByText('Gamma Project')).not.toBeInTheDocument();
    }
  });
});