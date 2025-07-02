# Identity Circuit Factory Frontend

A modern Next.js frontend for the Identity Circuit Factory system, built with TypeScript and Tailwind CSS.

## Features

-   **Modern UI**: Built with Next.js 14, TypeScript, and Tailwind CSS
-   **Interactive Navigation**: Seamless navigation between dimension groups, gate compositions, and representative circuits
-   **Circuit Visualization**: Detailed circuit views with ASCII diagrams, hamming distance plots, truth tables, and gate sequences
-   **Real-time Data**: Live connection to the backend API with automatic updates
-   **Responsive Design**: Works on desktop, tablet, and mobile devices
-   **Dark/Light Theme**: Glassmorphism design with modern visual effects

## Architecture

The frontend follows a hierarchical navigation structure:

1. **Dimension Groups** → List all dimension groups (width, gate_count combinations)
2. **Gate Compositions** → Show different gate compositions within a dimension group
3. **Representatives** → Display representative circuits for a specific composition
4. **Circuit Details** → In-depth view of a single circuit with visualization

## Prerequisites

-   Node.js 18+
-   npm or yarn
-   Backend API server running on `http://localhost:8000`

## Installation

1. **Install dependencies:**

    ```bash
    cd frontend-next
    npm install
    ```

2. **Set up environment variables (optional):**

    ```bash
    # Create .env.local file
    NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
    ```

3. **Run the development server:**

    ```bash
    npm run dev
    ```

4. **Open in browser:**
   Navigate to `http://localhost:3000`

## Development Scripts

```bash
# Start development server
npm run dev

# Build for production
npm run build

# Start production server
npm start

# Lint code
npm run lint
```

## Project Structure

```
frontend-next/
├── src/
│   ├── app/                 # Next.js app router
│   │   ├── globals.css      # Global styles
│   │   ├── layout.tsx       # Root layout
│   │   └── page.tsx         # Main page
│   ├── components/          # React components
│   │   ├── Header.tsx       # App header
│   │   ├── Sidebar.tsx      # Control sidebar
│   │   ├── MainContent.tsx  # Main navigation logic
│   │   ├── DimensionGroupsTable.tsx
│   │   ├── GateCompositionsTable.tsx
│   │   ├── RepresentativesTable.tsx
│   │   └── CircuitDetails.tsx
│   ├── lib/                 # Utilities
│   │   └── api.ts           # API client
│   └── types/               # TypeScript types
│       └── api.ts           # API type definitions
├── package.json
├── tsconfig.json
├── tailwind.config.js
├── next.config.js
└── README.md
```

## API Integration

The frontend communicates with the backend through a comprehensive API client (`src/lib/api.ts`) that provides:

-   **Health Checks**: Monitor backend status
-   **Statistics**: Factory and generation statistics
-   **Dimension Groups**: CRUD operations for dimension groups
-   **Gate Compositions**: Retrieve circuits by gate composition
-   **Circuit Management**: Get circuit details and visualizations
-   **Generation**: Trigger new circuit generation
-   **Debug Tools**: Enable/disable debug logging

## Components Overview

### Header

Displays the application title and branding.

### Sidebar

Contains:

-   Circuit generation controls
-   Debug tools
-   Factory statistics
-   Quick actions

### MainContent

Handles the main navigation flow:

-   Manages view state (dimension groups → compositions → representatives → details)
-   Implements breadcrumb navigation
-   Coordinates data loading and error handling

### Data Tables

-   **DimensionGroupsTable**: Lists all dimension groups with filtering
-   **GateCompositionsTable**: Shows gate compositions within a dimension group
-   **RepresentativesTable**: Displays representative circuits for a composition

### CircuitDetails

Comprehensive circuit visualization including:

-   ASCII circuit diagram
-   Hamming distance chart (using Chart.js)
-   Truth table
-   Gate sequence
-   Circuit metadata

## Styling

The application uses:

-   **Tailwind CSS**: Utility-first CSS framework
-   **Glassmorphism**: Modern glass-like visual effects
-   **Custom Components**: Reusable styled components
-   **Responsive Design**: Mobile-first approach

Key style features:

-   Glass panel effects with backdrop blur
-   Gradient backgrounds
-   Interactive hover states
-   Consistent color scheme
-   Modern typography

## API Endpoints Used

-   `GET /api/v1/health` - Health check
-   `GET /api/v1/stats` - Factory statistics
-   `GET /api/v1/dim-groups` - List dimension groups
-   `GET /api/v1/dim-groups/{id}/compositions` - Gate compositions
-   `GET /api/v1/dim-groups/{id}/circuits` - Circuits in dimension group
-   `GET /api/v1/circuits/{id}` - Circuit details
-   `GET /api/v1/circuits/{id}/visualization` - Circuit visualization
-   `POST /api/v1/generate` - Generate new circuit
-   `POST /api/v1/debug/enable-logging` - Enable debug logging
-   `POST /api/v1/debug/disable-logging` - Disable debug logging

## Configuration

### Environment Variables

-   `NEXT_PUBLIC_API_BASE_URL`: Backend API URL (default: http://localhost:8000)

### Next.js Configuration

The `next.config.js` includes:

-   API proxy rewrites for development
-   Experimental app directory support
-   Environment variable configuration

### Tailwind Configuration

Custom Tailwind configuration includes:

-   Extended color palette
-   Custom gradient backgrounds
-   Glass effect utilities
-   Custom box shadows

## Development Workflow

1. **Start the backend**: Ensure the Identity Circuit Factory API is running
2. **Install dependencies**: `npm install`
3. **Start development**: `npm run dev`
4. **Make changes**: Edit components, styles, or API integration
5. **Test locally**: Verify functionality in browser
6. **Build for production**: `npm run build`

## Troubleshooting

### Common Issues

1. **API Connection Errors**:

    - Verify backend is running on port 8000
    - Check CORS settings in backend
    - Confirm API endpoints are accessible

2. **Type Errors**:

    - Ensure all dependencies are installed
    - Check TypeScript configuration
    - Verify API type definitions match backend

3. **Styling Issues**:
    - Ensure Tailwind CSS is properly configured
    - Check for conflicting CSS rules
    - Verify custom component styles

### Development Tips

-   Use React DevTools for component debugging
-   Check browser network tab for API request issues
-   Use TypeScript strict mode for better error detection
-   Test responsive design at different screen sizes

## Browser Support

-   Chrome 88+
-   Firefox 85+
-   Safari 14+
-   Edge 88+

## Performance Considerations

-   Lazy loading for large circuit lists
-   Efficient API caching
-   Optimized chart rendering
-   Responsive image loading
-   Code splitting with Next.js

## Contributing

1. Follow TypeScript best practices
2. Use Tailwind CSS for styling
3. Implement responsive design
4. Add proper error handling
5. Write meaningful component documentation
6. Test across different browsers and devices
