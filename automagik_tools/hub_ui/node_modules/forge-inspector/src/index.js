import { ForgeInspector as Component } from './ForgeInspector.js'

export const ForgeInspector =
  process.env.NODE_ENV === 'development' ? Component : () => null
