import '@testing-library/jest-dom'

// jsdom doesn't implement ResizeObserver — Recharts needs it
class ResizeObserverMock {
  observe() {}
  unobserve() {}
  disconnect() {}
}
global.ResizeObserver = ResizeObserverMock
