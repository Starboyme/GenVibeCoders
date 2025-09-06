import React from 'react'
import Link from 'next/link'

const links = [
  {
    href: "/about",
    title: "About"
  },
  {
    href: "/docs",
    title: "Docs"
  }
];

const Navbar = ({isLoginPage} : {
  isLoginPage: boolean
}) => {
  return (
    <div className='flex items-center justify-between px-5 py-5'>
      <div className='flex items-center'>
        <svg
          className="h-8 w-8 text-sky-500"
          fill="none"
          viewBox="0 0 48 48"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            d="M44 11.2727C44 14.0109 39.8386 16.3957 33.69 17.6364C39.8386 18.877 44 21.2618 44 24C44 26.7382 39.8386 29.123 33.69 30.3636C39.8386 31.6043 44 33.9891 44 36.7273C44 40.7439 35.0457 44 24 44C12.9543 44 4 40.7439 4 36.7273C4 33.9891 8.16144 31.6043 14.31 30.3636C8.16144 29.123 4 26.7382 4 24C4 21.2618 8.16144 18.877 14.31 17.6364C8.16144 16.3957 4 14.0109 4 11.2727C4 7.25611 12.9543 4 24 4C35.0457 4 44 7.25611 44 11.2727Z"
            fill="currentColor"
          ></path>
        </svg>
        <h1 className="text-2xl font-bold tracking-tighter cursor-pointer text-gray-900 pl-2"><Link href="/">Tripmate</Link></h1>
      </div>
      <div className="flex items-center gap-5 text-lg text-neutral-800 font-semibold hover:text-neutral-600 transition duration-200">
      {links.map((link, index) => (
        <Link href={link.href} key={index}>
          {link.title}
        </Link>
      ))}
      
      {!isLoginPage && (
        <Link href="/login" key="login1">
          <button className='bg-sky-500 px-4 py-2 rounded-lg text-white text-md shadow-lg text-shadow-md tracking-wide cursor-pointer hover:bg-sky-600 transition-colors duration-200'>
            Sign In/Up
          </button>
        </Link>
      )}
      </div>
    </div>
  )
}

export default Navbar;