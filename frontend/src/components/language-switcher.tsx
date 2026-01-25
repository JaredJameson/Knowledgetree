/**
 * Language Switcher Component
 * Toggle between Polish and English
 */

import { Languages } from "lucide-react"
import { Button } from "@/components/ui/button"
import { useTranslation } from "react-i18next"

export function LanguageSwitcher() {
  const { i18n } = useTranslation()

  const toggleLanguage = () => {
    const newLang = i18n.language === "pl" ? "en" : "pl"
    i18n.changeLanguage(newLang)
  }

  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={toggleLanguage}
      aria-label="Toggle language"
      title={`Switch to ${i18n.language === "pl" ? "English" : "Polski"}`}
    >
      <Languages className="h-5 w-5" />
      <span className="sr-only ml-2 text-xs font-medium">
        {i18n.language.toUpperCase()}
      </span>
    </Button>
  )
}
