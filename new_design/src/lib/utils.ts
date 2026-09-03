import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * Group a count for the active language.
 *
 * A bare `toLocaleString()` follows the *browser's* locale, so a French page on
 * an English machine rendered "1,111" where French wants a space. Passing the
 * language explicitly keeps the separator matched to the copy around it.
 */
export function formatCount(value: number, language: 'fr' | 'en'): string {
  return value.toLocaleString(language === 'en' ? 'en-US' : 'fr-FR')
}

/**
 * Localise the decimal separator of a pre-formatted amount such as "$278.8M".
 *
 * The API hands back a display string, and French writes the decimal with a
 * comma. Without this the hero read "$278.8M" while the KPI tile beside it --
 * which goes through the number formatter -- read "$278,8M".
 */
export function formatAmount(amount: string, language: 'fr' | 'en'): string {
  return language === 'fr' ? amount.replace('.', ',') : amount
}
