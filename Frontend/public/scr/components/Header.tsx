import { Button } from "@/components/ui/button";

const Header = () => {
  const scrollToSection = (sectionId: string) => {
    const element = document.getElementById(sectionId);
    if (element) {
      element.scrollIntoView({ 
        behavior: 'smooth',
        block: 'start'
      });
    }
  };

  return (
    <header className="w-full bg-background/95 backdrop-blur-sm border-b border-border sticky top-0 z-50">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center space-x-3">
            <img 
              src="/lovable-uploads/46ca89a7-72fc-479a-bd07-4512df57ce75.png" 
              alt="Simple.Tech Logo" 
              className="h-8 w-auto animate-float cursor-pointer"
              onClick={() => scrollToSection('hero')}
            />
          </div>
          
          <nav className="hidden md:flex items-center space-x-8">
            <button 
              onClick={() => scrollToSection('sobre')}
              className="text-muted-foreground hover:text-foreground transition-colors cursor-pointer bg-transparent border-none"
            >
              Sobre
            </button>
            <button 
              onClick={() => scrollToSection('funcionalidades')}
              className="text-muted-foreground hover:text-foreground transition-colors cursor-pointer bg-transparent border-none"
            >
              Funcionalidades
            </button>
            <button 
              onClick={() => scrollToSection('tecnologia')}
              className="text-muted-foreground hover:text-foreground transition-colors cursor-pointer bg-transparent border-none"
            >
              Tecnologia
            </button>
            <button 
              onClick={() => scrollToSection('contato')}
              className="text-muted-foreground hover:text-foreground transition-colors cursor-pointer bg-transparent border-none"
            >
              Contato
            </button>
          </nav>

          {/* Mobile Menu Button */}
          <div className="md:hidden">
            <Button 
              variant="ghost" 
              size="sm"
              onClick={() => scrollToSection('funcionalidades')}
              className="text-muted-foreground hover:text-foreground"
            >
              Menu
            </Button>
          </div>

          <Button 
            variant="default" 
            className="bg-gradient-simple hover:opacity-90 text-primary-foreground font-medium hidden sm:block"
          >
            Experimentar
          </Button>
        </div>
      </div>
    </header>
  );
};

export default Header;