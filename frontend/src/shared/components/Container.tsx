import type { ReactNode } from 'react'

type ContainerProps = {
  children: ReactNode
  className?: string
  id?: string
}

export default function Container({ children, className = '', id }: ContainerProps) {
  return (
    <div id={id} className={`mx-auto w-full max-w-6xl px-6 lg:px-10 ${className}`}>
      {children}
    </div>
  )
}
