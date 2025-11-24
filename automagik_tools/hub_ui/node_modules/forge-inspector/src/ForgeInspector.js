/**
 * @typedef {import('./types.js').ForgeInspector} Props
 * @typedef {import('./types.js').Coords} Coords
 */

import { FloatingPortal } from '@floating-ui/react'
import { html } from 'htm/react'
import * as React from 'react'


import { getDisplayNameForInstance } from './getDisplayNameFromReactInstance.js'
import { getPathToSource } from './getPathToSource.js'
import { getPropsForInstance } from './getPropsForInstance.js'
import { getReactInstancesForElement } from './getReactInstancesForElement.js'
import { getSourceForInstance } from './getSourceForInstance.js'
import { getUrl } from './getUrl.js'

export const State = /** @type {const} */ ({
  IDLE: 'IDLE',
  HOVER: 'HOVER',
  SELECT: 'SELECT',
})

export const Trigger = /** @type {const} */ ({
  ALT_KEY: 'alt-key',
  BUTTON: 'button',
})

// Message source and version for iframe communication
const MESSAGE_SOURCE = 'click-to-component'
const MESSAGE_VERSION = 1

/**
 * Extract component instances data for a target element
 * @param {HTMLElement} target
 * @param {import('./types.js').PathModifier} pathModifier
 * @returns {Array}
 */
function getComponentInstances(target, pathModifier) {
  if (!target) return []

  const instances = getReactInstancesForElement(target).filter((instance) =>
    getSourceForInstance(instance)
  )

  return instances.map((instance) => {
    const name = getDisplayNameForInstance(instance)
    const source = getSourceForInstance(instance)
    const path = getPathToSource(source, pathModifier)
    const props = getPropsForInstance(instance)

    return {
      name,
      props,
      source: {
        fileName: source.fileName,
        lineNumber: source.lineNumber,
        columnNumber: source.columnNumber
      },
      pathToSource: path
    }
  })
}

/**
 * Send a message to the parent window when opening in editor.
 * No-ops when not inside an iframe.
 * @param {Object} args
 * @param {string} args.editor
 * @param {string} args.pathToSource
 * @param {string} args.url
 * @param {'alt-click'|'context-menu'} args.trigger
 * @param {MouseEvent} [args.event]
 * @param {HTMLElement} [args.element]
 * @param {import('./types.js').PathModifier} [args.pathModifier]
 * @param {string} [args.selectedComponent] - Name of the selected component
 */
function postOpenToParent({ editor, pathToSource, url, trigger, event, element, pathModifier, selectedComponent }) {
  try {
    const el = element || (event && event.target instanceof HTMLElement ? event.target : null)

    // Get all component instances for the clicked element
    const allComponents = el ? getComponentInstances(el, pathModifier) : []

    // Find the selected component in the list (or use the first one)
    const selected = selectedComponent
      ? allComponents.find(comp => comp.name === selectedComponent)
      : allComponents.find(comp => comp.pathToSource === pathToSource) || allComponents[0]

    const elementInfo = el
      ? {
        tag: el.tagName?.toLowerCase?.() || undefined,
        id: el.id || undefined,
        className:
          typeof el.className === 'string'
            ? el.className
            : String(el.className || ''),
        role: el.getAttribute('role') || undefined,
        dataset: { ...el.dataset },
      }
      : undefined

    const message = {
      source: MESSAGE_SOURCE,
      version: MESSAGE_VERSION,
      type: 'open-in-editor',
      payload: {
        selected: selected ? {
          editor,
          pathToSource: selected.pathToSource,
          url,
          name: selected.name,
          props: selected.props,
          source: selected.source
        } : {
          editor,
          pathToSource,
          url,
          name: selectedComponent || 'Unknown',
          props: {},
          source: {}
        },
        components: allComponents,
        trigger,
        coords: event
          ? { x: event.clientX ?? undefined, y: event.clientY ?? undefined }
          : undefined,
        clickedElement: elementInfo,
      },
    }

    if (
      typeof window !== 'undefined' &&
      window.parent &&
      window.parent !== window &&
      typeof window.parent.postMessage === 'function'
    ) {
      window.parent.postMessage(message, '*') // dev-only, permissive
    }
  } catch (err) {
    // Never break product flows due to messaging
    console.warn('[click-to-component] postMessage failed', err)
  }
}

/**
 * ForgeInspector component for click-to-edit functionality
 */
export function ForgeInspector() {
  const editor = 'vscode' // legacy
  const pathModifier = (path) => path // legacy
  const [state, setState] = React.useState(
    /** @type {State[keyof State]} */
    (State.IDLE)
  )

  const [trigger, setTrigger] = React.useState(
    /** @type {Trigger[keyof Trigger] | null} */
    (null)
  )

  const [target, setTarget] = React.useState(
    /** @type {HTMLElement | null} */
    (null)
  )

  const [showButton, setShowButton] = React.useState(false)



  const fiIcon = `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="22" x2="18" y1="12" y2="12"/><line x1="6" x2="2" y1="12" y2="12"/><line x1="12" x2="12" y1="6" y2="2"/><line x1="12" x2="12" y1="22" y2="18"/></svg>`;

  const TargetButton = React.useCallback(
    ({ active, onToggle }) => html`
      <button
        onClick=${function handleButtonClick(e) {
        e.stopPropagation()
        onToggle()
      }}
        aria-pressed=${active}
        style=${{
        position: 'fixed',
        bottom: '16px',
        right: '16px',
        width: '48px',
        height: '48px',
        borderRadius: '50%',
        background: active ? 'royalblue' : 'white',
        color: active ? 'white' : 'black',
        border: '1px solid #ccc',
        boxShadow: '0 2px 6px rgba(0,0,0,.3)',
        zIndex: 2147483647,
        cursor: 'pointer',
        fontSize: '18px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '8px',
      }}
        title="Toggle targeting mode"
      >
        <img
          src=${'data:image/svg+xml;utf8,' + encodeURIComponent(fiIcon)}
          alt="FI Icon"
          style=${{
        width: '32px',
        height: '32px',
        filter: active ? 'brightness(0) invert(1)' : 'none',
      }}
        />
      </button>
    `,
    []
  )

  const toggleTargeting = React.useCallback(() => {
    if (state === State.HOVER && trigger === Trigger.BUTTON) {
      setState(State.IDLE)
      setTrigger(null)
    } else {
      setState(State.HOVER)
      setTrigger(Trigger.BUTTON)
    }
  }, [state, trigger])

  const onContextMenu = React.useCallback(
    function handleContextMenu(
      /**
       * @type {MouseEvent}
       */
      event
    ) {
      // Only interfere when the tool is active
      if (state !== State.IDLE && event.target instanceof HTMLElement) {
        event.preventDefault()

        // Optional: notify the parent for visualization
        postOpenToParent({
          editor,
          pathToSource: '',
          url: '',
          trigger: 'context-menu',
          event,
          element: event.target,
          pathModifier
        })
      }
    },
    [state, editor, pathModifier]
  )

  const onClick = React.useCallback(
    function handleClick(
      /**
       * @type {MouseEvent}
       */
      event
    ) {
      // Prevent all default actions when targeting is active
      if (state === State.HOVER) {
        event.preventDefault()
        event.stopPropagation()
      }

      // Handle targeting mode click (left-click sends message to parent)
      if (state === State.HOVER && trigger === Trigger.BUTTON && target instanceof HTMLElement) {

        // Notify parent window with component info
        postOpenToParent({
          editor,
          pathToSource: '', // Will be determined when user selects
          url: '',
          trigger: 'context-menu',
          event,
          element: target,
          pathModifier,
        })

        setState(State.IDLE)
        setTrigger(null)
        return
      }

      // Handle Alt+click mode (use postMessage instead of navigation)
      if (state === State.HOVER && trigger === Trigger.ALT_KEY && target instanceof HTMLElement) {
        const instance = getReactInstancesForElement(target).find((instance) =>
          getSourceForInstance(instance)
        )

        if (!instance) {
          return console.warn(
            'Could not find React instance for element',
            target
          )
        }

        const source = getSourceForInstance(instance)

        if (!source) {
          return console.warn(
            'Could not find source for React instance',
            instance
          )
        }
        const path = getPathToSource(source, pathModifier)
        const url = getUrl({
          editor,
          pathToSource: path,
        })

        event.preventDefault()

        // Use postMessage instead of direct navigation
        postOpenToParent({
          editor,
          pathToSource: path,
          url,
          trigger: 'alt-click',
          event,
          element: target,
          pathModifier
        })

        setState(State.IDLE)
        setTrigger(null)
      }
    },
    [editor, pathModifier, state, trigger, target]
  )



  const onKeyDown = React.useCallback(
    function handleKeyDown(
      /**
       * @type {KeyboardEvent}
       */
      event
    ) {
      switch (state) {
        case State.IDLE:
          if (event.altKey) {
            setState(State.HOVER)
            setTrigger(Trigger.ALT_KEY)
          }
          break

        case State.HOVER:
          if (event.key === 'Escape' && trigger === Trigger.BUTTON) {
            setState(State.IDLE)
            setTrigger(null)
          }
          break

        default:
      }
    },
    [state, trigger]
  )

  const onKeyUp = React.useCallback(
    function handleKeyUp(
      /**
       * @type {KeyboardEvent}
       */
      event
    ) {
      switch (state) {
        case State.HOVER:
          if (trigger === Trigger.ALT_KEY) {
            setState(State.IDLE)
            setTrigger(null)
          }
          break

        default:
      }
    },
    [state, trigger]
  )

  const onMouseMove = React.useCallback(
    function handleMouseMove(
      /** @type {MouseEvent} */
      event
    ) {
      if (!(event.target instanceof HTMLElement)) {
        return
      }

      switch (state) {
        case State.IDLE:
        case State.HOVER:
          setTarget(event.target)
          break

        default:
          break
      }
    },
    [state]
  )

  const onBlur = React.useCallback(
    function handleBlur() {
      switch (state) {
        case State.HOVER:
          setState(State.IDLE)
          setTrigger(null)
          break

        default:
      }
    },
    [state]
  )

  React.useEffect(
    function toggleIndicator() {
      for (const element of Array.from(
        document.querySelectorAll('[data-click-to-component-target]')
      )) {
        if (element instanceof HTMLElement) {
          delete element.dataset.clickToComponentTarget
        }
      }

      if (state === State.IDLE) {
        delete window.document.body.dataset.clickToComponent
        window.document.body.style.removeProperty('--click-to-component-cursor')
        if (target) {
          delete target.dataset.clickToComponentTarget
        }
        return
      }

      if (target instanceof HTMLElement) {
        window.document.body.dataset.clickToComponent = state
        target.dataset.clickToComponentTarget = state

        // Set cursor to crosshair for targeting
        window.document.body.style.setProperty(
          '--click-to-component-cursor',
          'crosshair'
        )
      }
    },
    [state, target, trigger]
  )

  // Listen for enable-button message from parent
  React.useEffect(function listenForEnableButton() {
    if (typeof window === 'undefined') return
    function onMessage(event) {
      const data = event?.data
      if (
        data &&
        data.source === MESSAGE_SOURCE &&
        data.version === MESSAGE_VERSION &&
        data.type === 'enable-button'
      ) {
        setShowButton(true)
      }
    }
    window.addEventListener('message', onMessage)
    return () => window.removeEventListener('message', onMessage)
  }, [])

  // Send ready message to parent when component mounts
  React.useEffect(function sendReadyMessage() {
    if (
      typeof window !== 'undefined' &&
      window.parent &&
      window.parent !== window &&
      typeof window.parent.postMessage === 'function'
    ) {
      try {
        window.parent.postMessage(
          {
            source: MESSAGE_SOURCE,
            version: MESSAGE_VERSION,
            type: 'ready'
          },
          '*'
        )
      } catch (err) {
        console.warn('[click-to-component] ready message failed', err)
      }
    }
  }, [])

  React.useEffect(
    function addEventListenersToWindow() {
      window.addEventListener('click', onClick, { capture: true })
      window.addEventListener('contextmenu', onContextMenu, { capture: true })
      window.addEventListener('keydown', onKeyDown)
      window.addEventListener('keyup', onKeyUp)
      window.addEventListener('mousemove', onMouseMove)
      window.addEventListener('blur', onBlur)

      return function removeEventListenersFromWindow() {
        window.removeEventListener('click', onClick, { capture: true })
        window.removeEventListener('contextmenu', onContextMenu, {
          capture: true,
        })
        window.removeEventListener('keydown', onKeyDown)
        window.removeEventListener('keyup', onKeyUp)
        window.removeEventListener('mousemove', onMouseMove)
        window.removeEventListener('blur', onBlur)
      }
    },
    [onClick, onContextMenu, onKeyDown, onKeyUp, onMouseMove, onBlur]
  )

  return html`
    <style key="click-to-component-style">
      [data-click-to-component] * {
        pointer-events: auto !important;
      }

      [data-click-to-component-target] {
        cursor: var(--click-to-component-cursor, crosshair) !important;
        outline: auto 1px;
        outline: var(
          --click-to-component-outline,
          -webkit-focus-ring-color auto 1px
        ) !important;
      }
    </style>

    ${showButton && html`
      <${FloatingPortal} key="click-to-component-portal">
        <${TargetButton}
          key="click-to-component-target-button"
          active=${state === State.HOVER && trigger === Trigger.BUTTON}
          onToggle=${toggleTargeting}
        />
      </${FloatingPortal}>
    `}
  `
}
