import { Github, Mail, ExternalLink } from "lucide-react";
import { Button } from "@/components/ui/button";

const Footer = () => {
  return (
    <footer id="contato" className="bg-background border-t border-border">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="grid md:grid-cols-3 gap-8 mb-8">
          {/* Logo and Description */}
          <div className="space-y-4">
            <div className="flex items-center space-x-3">
              <img 
                src="/lovable-uploads/46ca89a7-72fc-479a-bd07-4512df57ce75.png" 
                alt="Simple.Tech Logo" 
                className="h-8 w-auto"
              />
            </div>
            <p className="text-muted-foreground leading-relaxed">
              Democratizando o acesso à inteligência artificial através de soluções 
              simples e poderosas para análise de risco.
            </p>
          </div>

          {/* Quick Links */}
          <div>
            <h3 className="text-foreground font-semibold mb-4">Links Rápidos</h3>
            <nav className="space-y-2">
              <a 
                href="#sobre" 
                className="block text-muted-foreground hover:text-foreground transition-colors"
              >
                Sobre o Projeto
              </a>
              <a 
                href="#funcionalidades" 
                className="block text-muted-foreground hover:text-foreground transition-colors"
              >
                Funcionalidades
              </a>
              <a 
                href="#tecnologia" 
                className="block text-muted-foreground hover:text-foreground transition-colors"
              >
                Tecnologias
              </a>
              <a 
                href="https://github.com/2off2/Simple.Tech" 
                target="_blank" 
                rel="noopener noreferrer"
                className="inline-flex items-center text-muted-foreground hover:text-foreground transition-colors"
              >
                Código Fonte
                <ExternalLink className="ml-1 h-3 w-3" />
              </a>
            </nav>
          </div>

          {/* Contact */}
          <div>
            <h3 className="text-foreground font-semibold mb-4">Contato</h3>
            <div className="space-y-4">
              <p className="text-muted-foreground">
                Projeto desenvolvido para o curso técnico de Inteligência Artificial
              </p>
              
              <div className="flex space-x-3">
                <Button 
                  variant="outline" 
                  size="sm" 
                  className="border-border hover:bg-accent/10"
                  asChild
                >
                  <a 
                    href="https://github.com/2off2/Simple.Tech" 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="inline-flex items-center"
                  >
                    <Github className="h-4 w-4 mr-2" />
                    GitHub
                  </a>
                </Button>
                
                <Button 
                  variant="outline" 
                  size="sm" 
                  className="border-border hover:bg-accent/10"
                  asChild
                >
                  <a 
                    href="mailto:contato@simpletech.com" 
                    className="inline-flex items-center"
                  >
                    <Mail className="h-4 w-4 mr-2" />
                    Email
                  </a>
                </Button>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="border-t border-border pt-8">
          <div className="flex flex-col md:flex-row justify-between items-center space-y-4 md:space-y-0">
            <p className="text-muted-foreground text-sm">
              © 2024 Simple.Tech. Projeto Técnico Integrador - Curso de Inteligência Artificial
            </p>
            
            <div className="flex items-center space-x-4 text-sm text-muted-foreground">
              <span>Feito com</span>
              <span className="text-primary animate-pulse">♥</span>
              <span>para democratizar a IA</span>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;