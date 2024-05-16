"use client";

import Image from "next/image";
import styles from "./page.module.css";
import { FormEvent, useState, useEffect } from "react";

export default function Home() {
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [formState, setFormState] = useState({email: ''});
  const [isErrorActive, setIsErrorActive] = useState(false);

  useEffect(() => {
    setTimeout(() => {
      setIsErrorActive(false)
    }, 3000)
  }, [isErrorActive])

  const handleSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    console.log(formState);
    setIsSubmitted(true);
  }

  return (
    <main className={styles.main}>
      <div className={styles.toast} style={{display: isErrorActive ? 'block' : 'none'}}>
        <p>Error encountered while signing up.  Please try again.</p>
      </div>
      <form onSubmit={e => handleSubmit(e)} style={{display: isSubmitted ? 'none' : 'block'}}>
        <label htmlFor="email" className={styles.emailLabel}>Enter your email</label>
        <input type="email" name="email" id="email" onChange={e => setFormState({email: e.target.value})} />
        <button type="submit" className={styles.submitButton}>Submit</button>
      </form>
      <div style={{display: isSubmitted ? 'block' : 'none'}}>
        <p>Thanks for signing up. Get ready to receive actionable climate news in your inbox every morning!</p>
      </div>
    </main>
  );
}