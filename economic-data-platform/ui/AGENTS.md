<!-- BEGIN:nextjs-agent-rules -->
# This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` before writing any code. Heed deprecation notices.
<!-- END:nextjs-agent-rules -->

# ui/ — Next.js Frontend Dashboard

## OVERVIEW

Next.js app (App Router) with shadcn/ui + Tailwind CSS. Serves as the analytics dashboard for the Economic Data Platform. This is the **active** frontend — `image/` is stale.

## STRUCTURE

```
ui/
├── app/
│   ├── layout.tsx          # Root layout
│   ├── page.tsx            # Home page
│   ├── globals.css         # Global styles
│   ├── api/                # Next.js API routes (proxy/BFF)
│   └── reports/            # Report pages
├── components/
│   ├── ui/                 # shadcn/ui components (17 components)
│   ├── reports/            # Report-specific components
│   ├── providers/          # React context providers
│   └── sidebar.tsx         # Navigation sidebar
├── lib/
│   ├── data.ts             # Data fetching functions
│   ├── db.ts               # Database connection helpers
│   ├── schemas.ts          # Zod validation schemas
│   ├── types.ts            # TypeScript type definitions
│   └── utils.ts            # General utilities (cn() etc.)
├── public/                 # Static assets
├── components.json         # shadcn/ui config
├── next.config.ts          # Next.js configuration
└── package.json            # Dependencies
```

## CONVENTIONS

- shadcn/ui components live in `components/ui/` — add new ones via `npx shadcn@latest add`
- Data fetching in `lib/data.ts`, types in `lib/types.ts`
- App Router with `app/` directory (not Pages Router)
- `lib/utils.ts` exports `cn()` for Tailwind class merging

## ANTI-PATTERNS

- Do NOT modify the `image/` directory — it's a legacy app with screenshots
- This `ui/` has its own `.git/` — it may be a git submodule or separate repo
