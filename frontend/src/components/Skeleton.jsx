import React from 'react';

// Base shimmer block
export function Shimmer({ className = '', rounded = 'rounded-xl' }) {
  return <div className={`shimmer ${rounded} ${className}`} />;
}

// Skeleton for a stat card (gradient card shape)
export function StatCardSkeleton() {
  return (
    <div className="rounded-2xl p-5" style={{ background: 'rgba(255,255,255,0.70)', backdropFilter: 'blur(16px)', border: '1px solid rgba(255,255,255,0.60)' }}>
      <div className="flex items-center justify-between">
        <div className="flex-1 space-y-3">
          <Shimmer className="h-3 w-24" />
          <Shimmer className="h-8 w-20" />
        </div>
        <Shimmer className="h-12 w-12 rounded-xl" />
      </div>
    </div>
  );
}

// Skeleton for the alerts panel
export function AlertSkeleton() {
  return (
    <div className="glass-card rounded-2xl p-6">
      <div className="flex items-center justify-between mb-5">
        <Shimmer className="h-5 w-32" />
        <Shimmer className="h-4 w-16" />
      </div>
      <div className="space-y-3">
        {[0, 1, 2].map(i => (
          <div key={i} className="p-3 rounded-xl border border-slate-200/60">
            <div className="flex items-start justify-between">
              <div className="flex-1 space-y-2">
                <Shimmer className="h-4 w-28" />
                <Shimmer className="h-3 w-full" />
                <Shimmer className="h-3 w-3/4" />
              </div>
              <Shimmer className="h-5 w-14 rounded-full" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// Skeleton for PHC health score rows
export function PHCScoreSkeleton() {
  return (
    <div className="glass-card rounded-2xl p-6">
      <Shimmer className="h-5 w-40 mb-5" />
      <div className="space-y-3">
        {[0, 1, 2, 3].map(i => (
          <div key={i} className="p-4 rounded-xl border border-slate-200/60">
            <div className="flex items-center justify-between">
              <div className="flex-1 space-y-3">
                <div className="flex items-center gap-3">
                  <Shimmer className="h-2.5 w-2.5 rounded-full" />
                  <Shimmer className="h-4 w-32" />
                  <Shimmer className="h-5 w-16 rounded-full" />
                </div>
                <div className="flex gap-4">
                  <Shimmer className="h-3 w-20" />
                  <Shimmer className="h-3 w-20" />
                  <Shimmer className="h-3 w-20" />
                </div>
              </div>
              <div className="flex items-center gap-3">
                <Shimmer className="h-8 w-12" />
                <Shimmer className="h-4 w-4 rounded-full" />
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// Skeleton for chart areas
export function ChartSkeleton({ height = 300 }) {
  return (
    <div className="glass-card rounded-2xl p-6">
      <Shimmer className="h-5 w-48 mb-5" />
      <div className="flex items-end gap-3" style={{ height }}>
        {['40%', '65%', '50%', '80%', '55%', '70%', '45%'].map((h, i) => (
          <div key={i} style={{ height: h, flex: 1 }}>
            <Shimmer className="h-full w-full" rounded="rounded-lg" />
          </div>
        ))}
      </div>
    </div>
  );
}

// ===== Page-specific skeleton layouts =====

export function DashboardSkeleton() {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 animate-fade-in">
      {/* Header */}
      <div className="mb-8 space-y-3">
        <Shimmer className="h-6 w-20 rounded-full" />
        <Shimmer className="h-10 w-80" />
        <Shimmer className="h-4 w-64" />
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5 mb-8">
        {[0, 1, 2, 3].map(i => (
          <div key={i} className="animate-fade-in-up" style={{ animationDelay: `${i * 0.05}s` }}>
            <StatCardSkeleton />
          </div>
        ))}
      </div>

      {/* Alerts + PHC scores */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 mb-8">
        <AlertSkeleton />
        <div className="lg:col-span-2">
          <PHCScoreSkeleton />
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <ChartSkeleton />
        <ChartSkeleton />
      </div>
    </div>
  );
}

export function AlertsSkeleton() {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 animate-fade-in">
      <div className="mb-8 space-y-3">
        <Shimmer className="h-10 w-48" />
        <Shimmer className="h-4 w-56" />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-5 mb-8">
        {[0, 1, 2, 3].map(i => <StatCardSkeleton key={i} />)}
      </div>

      <div className="flex gap-2 mb-6">
        {[0, 1, 2, 3].map(i => (
          <Shimmer key={i} className="h-9 w-24 rounded-full" />
        ))}
      </div>

      <div className="glass-card rounded-2xl p-6">
        <div className="space-y-3">
          {[0, 1, 2, 3, 4].map(i => (
            <div key={i} className="p-4 rounded-xl border border-slate-200/60">
              <div className="flex items-start justify-between">
                <div className="flex-1 space-y-2">
                  <Shimmer className="h-4 w-32" />
                  <Shimmer className="h-3 w-full" />
                  <Shimmer className="h-3 w-2/3" />
                </div>
                <Shimmer className="h-6 w-16 rounded-full" />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export function RecommendationsSkeleton() {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 animate-fade-in">
      <div className="mb-8 space-y-3">
        <Shimmer className="h-10 w-56" />
        <Shimmer className="h-4 w-72" />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-5 mb-8">
        {[0, 1, 2].map(i => <StatCardSkeleton key={i} />)}
      </div>

      <div className="space-y-4">
        {[0, 1, 2, 3].map(i => (
          <div key={i} className="glass-card rounded-2xl p-6">
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1 space-y-3">
                <div className="flex items-center gap-3">
                  <Shimmer className="h-5 w-16 rounded-full" />
                  <Shimmer className="h-5 w-20 rounded-full" />
                </div>
                <Shimmer className="h-4 w-full" />
                <Shimmer className="h-4 w-3/4" />
                <div className="flex gap-6 pt-2">
                  <Shimmer className="h-3 w-24" />
                  <Shimmer className="h-3 w-24" />
                </div>
              </div>
              <Shimmer className="h-10 w-10 rounded-xl" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export function PHCDetailSkeleton() {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 animate-fade-in">
      <div className="mb-8 space-y-3">
        <div className="flex items-center gap-3">
          <Shimmer className="h-2.5 w-2.5 rounded-full" />
          <Shimmer className="h-8 w-40" />
          <Shimmer className="h-6 w-20 rounded-full" />
        </div>
        <Shimmer className="h-4 w-48" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 mb-8">
        {/* Health score card */}
        <div className="glass-card rounded-2xl p-6">
          <Shimmer className="h-5 w-32 mb-4" />
          <Shimmer className="h-20 w-20 rounded-full mx-auto mb-4" />
          <div className="space-y-3">
            {[0, 1, 2, 3].map(i => (
              <div key={i} className="flex items-center justify-between">
                <Shimmer className="h-3 w-24" />
                <Shimmer className="h-3 w-12" />
              </div>
            ))}
          </div>
        </div>

        {/* Charts */}
        <div className="lg:col-span-2 space-y-5">
          <ChartSkeleton height={200} />
          <ChartSkeleton height={200} />
        </div>
      </div>

      {/* Stock table */}
      <div className="glass-card rounded-2xl p-6">
        <Shimmer className="h-5 w-32 mb-5" />
        <div className="space-y-3">
          {[0, 1, 2, 3, 4, 5].map(i => (
            <div key={i} className="flex items-center justify-between p-3 rounded-xl border border-slate-200/60">
              <div className="flex items-center gap-4 flex-1">
                <Shimmer className="h-5 w-32" />
                <Shimmer className="h-4 w-16" />
              </div>
              <div className="flex items-center gap-4">
                <Shimmer className="h-4 w-12" />
                <Shimmer className="h-5 w-16 rounded-full" />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
