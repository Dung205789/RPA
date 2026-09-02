import org.openqa.selenium.*;
import org.openqa.selenium.interactions.Actions;
import java.util.Set;
import java.util.ArrayList;

public class GeneratedTest {
    public static void main(String[] args) {
        WebDriver driver = new ChromeDriver();
        Actions actions = new Actions(driver);

        driver.get("https://app.diagrams.net/");

        driver.findElement(By.xpath("/html/body/div[3]/div[1]/div[4]/div/a[5]")).click();

        WebElement object1 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(32)"));
        object1.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_LEFT).keyUp(Keys.SHIFT).perform(); }

        WebElement object6 = driver.findElement(By.xpath("//not-found"));
        object6.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_LEFT).keyUp(Keys.SHIFT).perform(); }

        driver.findElement(By.xpath("/html/body/div[3]/div[1]/div[4]/div/a[1]")).click();

        WebElement object7 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(32)"));
        WebElement relatedObject1 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(33)"));
        actions.moveToElement(object7, 0, object7.getSize().getHeight() / 2)
                .clickAndHold()
                .moveToElement(relatedObject1, 0, -relatedObject1.getSize().getHeight() / 2)
                .release()
                .perform();

        WebElement object12 = driver.findElement(By.xpath("//not-found"));
        actions.doubleClick(object12).perform();

        WebElement textBox = driver.switchTo().activeElement();
        textBox.sendKeys("yes");

        driver.quit();
    }
}