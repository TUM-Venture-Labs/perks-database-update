# Venture Labs Dashboard

A comprehensive Next.js dashboard for managing startup perks database and pitchdeck analysis at UnternehmerTUM Venture Labs.

## Features

### 🏠 Dashboard Overview
- Real-time statistics and KPIs
- System status monitoring
- Recent activity feed
- Quick action buttons for common tasks

### 💼 Perks Database Management
- **Interactive perks table** with search and filtering
- **Status monitoring** (active, error, pending updates)
- **Add new perks** with URL scraping capability
- **Bulk operations** for running scrapers
- **Individual perk management** with manual refresh options
- **Real-time status updates** and last-updated timestamps

### 📊 Pitchdeck Analyzer
- **Application pipeline management** with status tracking
- **AI-powered analysis** with confidence scores
- **Requirements matching** against program criteria
- **Due diligence automation** with external source validation
- **Manual review interface** with approve/reject actions
- **Team collaboration** through comments system
- **Analytics dashboard** with success rates by sector

### 🔧 Technical Features
- **Responsive design** with mobile support
- **Real-time updates** and status monitoring
- **Search and filtering** across all data
- **Export capabilities** for reports
- **Modern UI components** with Tailwind CSS
- **TypeScript** for type safety

## UI Interaction Patterns Implemented

### Perks Database Scrapper Updater:
✅ **Dashboard Overview**: Status cards, last run timestamps, success/failure rates
✅ **Perks Management Table**: Sortable/filterable with individual and bulk actions
✅ **Add New Perk Flow**: URL input with validation and preview
✅ **Individual Perk Details**: Comprehensive view with edit capabilities and history
✅ **Real-time Status**: Visual indicators and progress tracking

### Pitchdeck Analyzer:
✅ **Applications Dashboard**: Pipeline visualization with status distribution
✅ **Queue Management**: Filterable table with bulk analysis capabilities
✅ **Individual Analysis View**: Side-by-side content and AI results
✅ **Manual Review Interface**: Approve/reject with comments system
✅ **Analytics & Reporting**: Success rates and trend analysis

## Project Structure

```
client/
├── app/                          # Next.js App Router
│   ├── page.tsx                 # Main dashboard
│   ├── perks/                   # Perks management
│   │   ├── page.tsx            # Perks list view
│   │   ├── [id]/               # Individual perk details
│   │   └── add/                # Add new perk (planned)
│   ├── pitchdecks/             # Pitchdeck analysis
│   │   ├── page.tsx            # Applications list
│   │   └── [id]/               # Individual application analysis
│   ├── layout.tsx              # Root layout with navigation
│   └── globals.css             # Global styles with design system
├── components/
│   ├── ui/                     # Reusable UI components
│   │   ├── button.tsx          # Button variants
│   │   └── card.tsx            # Card layouts
│   └── navigation.tsx          # Main navigation component
├── lib/
│   ├── utils.ts                # Utility functions
│   └── api.ts                  # API integration functions
└── tailwind.config.ts          # Tailwind configuration
```

## Technology Stack

- **Frontend**: Next.js 15 with React 18
- **Styling**: Tailwind CSS with custom design system
- **UI Components**: Radix UI primitives with custom styling
- **Icons**: Lucide React icons
- **TypeScript**: Full type safety throughout
- **API Integration**: RESTful calls to Python backend

## API Integration

The dashboard is designed to integrate with your Python backend through REST APIs. All API calls are centralized in `lib/api.ts`:

### Expected Endpoints:

#### Perks API:
- `GET /api/perks` - List all perks
- `POST /api/perks` - Add new perk
- `GET /api/perks/{id}` - Get perk details
- `PUT /api/perks/{id}` - Update perk
- `DELETE /api/perks/{id}` - Delete perk
- `POST /api/perks/scrape` - Run scraper for all perks
- `POST /api/perks/{id}/scrape` - Scrape specific perk

#### Pitchdecks API:
- `GET /api/pitchdecks` - List applications (with filters)
- `POST /api/pitchdecks/upload` - Upload new application
- `GET /api/pitchdecks/{id}` - Get application details
- `POST /api/pitchdecks/{id}/analyze` - Analyze application
- `PUT /api/pitchdecks/{id}/review` - Update review status
- `POST /api/pitchdecks/{id}/comments` - Add comment

#### System API:
- `GET /api/system/status` - System health status
- `GET /api/dashboard/stats` - Dashboard statistics
- `GET /api/dashboard/activity` - Recent activity

## Getting Started

1. **Install dependencies:**
   ```bash
   npm install --legacy-peer-deps
   ```

2. **Set up environment variables:**
   ```bash
   # .env.local
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

3. **Start development server:**
   ```bash
   npm run dev
   ```

4. **Open in browser:**
   Navigate to `http://localhost:3000`

## Configuration

### Environment Variables:
- `NEXT_PUBLIC_API_URL`: Your Python backend URL (default: http://localhost:8000)

### Customization:
- Colors and styling: Edit `app/globals.css` and `tailwind.config.ts`
- API endpoints: Modify `lib/api.ts`
- Navigation: Update `components/navigation.tsx`

## Features Ready for Backend Integration

### Immediate Integration Points:
1. **Replace mock data** in pages with actual API calls
2. **Connect scraper triggers** to your Python scraping logic
3. **Integrate analysis engine** with your LLM-based pitchdeck analyzer
4. **Add file upload** functionality for pitch decks
5. **Implement real-time updates** via WebSockets or polling

### Mock Data Locations:
- Dashboard stats: `app/page.tsx`
- Perks data: `app/perks/page.tsx`
- Applications data: `app/pitchdecks/page.tsx`
- Individual application: `app/pitchdecks/[id]/page.tsx`

## Deployment

The dashboard is ready for deployment on Vercel, Netlify, or any platform supporting Next.js applications.

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## Contributing

This dashboard serves as the frontend interface for your Venture Labs operations. To extend functionality:

1. Add new pages in the `app/` directory
2. Create reusable components in `components/`
3. Update API functions in `lib/api.ts`
4. Follow the existing UI patterns and styling conventions

---

Built with ❤️ for UnternehmerTUM Venture Labs
