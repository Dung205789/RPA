import org.openqa.selenium.*;
import org.openqa.selenium.interactions.Actions;
import java.util.Set;
import java.util.ArrayList;

public class GeneratedTest {
    public static void main(String[] args) {
        WebDriver driver = new ChromeDriver();
        Actions actions = new Actions(driver);

        driver.get("https://app.diagrams.net/");

        driver.findElement(By.xpath("//body/div[7]/div[1]/input[1]")).click();

        driver.findElement(By.xpath("/html/body/div[11]/table/tbody/tr[16]/td[2]")).click();

        driver.findElement(By.xpath("//body/div[3]/div[1]/div[4]/div[1]/a[5]")).click();

        WebElement object1 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(37)"));
        object1.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_LEFT).keyUp(Keys.SHIFT).perform(); }

        WebElement object2 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(37)"));
        object2.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_LEFT).keyUp(Keys.SHIFT).perform(); }

        WebElement object3 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(37)"));
        object3.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_LEFT).keyUp(Keys.SHIFT).perform(); }

        driver.findElement(By.xpath("//body/div[7]/div[1]/input[1]")).click();

        driver.findElement(By.xpath("/html/body/div[11]/table/tbody/tr[16]/td[2]")).click();

        driver.findElement(By.xpath("//body/div[3]/div[1]/div[4]/div[1]/a[1]")).click();

        WebElement object4 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(1) > g:nth-child(4)"));
        WebElement relatedObject1 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(38)"));
        actions.moveToElement(object4, 0, object4.getSize().getHeight() / 2)
                .clickAndHold()
                .moveToElement(relatedObject1, 0, -relatedObject1.getSize().getHeight() / 2)
                .release()
                .perform();

        driver.findElement(By.xpath("//body/div[7]/div[1]/input[1]")).click();

        driver.findElement(By.xpath("/html/body/div[11]/table/tbody/tr[16]/td[2]")).click();

        driver.findElement(By.xpath("//body/div[3]/div[1]/div[4]/div[1]/a[5]")).click();

        WebElement object9 = driver.findElement(By.xpath("//not-found"));
        object9.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_RIGHT).keyUp(Keys.SHIFT).perform(); }

        WebElement object14 = driver.findElement(By.xpath("//not-found"));
        object14.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_RIGHT).keyUp(Keys.SHIFT).perform(); }

        WebElement object19 = driver.findElement(By.xpath("//not-found"));
        object19.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_RIGHT).keyUp(Keys.SHIFT).perform(); }

        WebElement object20 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(39)"));
        WebElement relatedObject2 = driver.findElement(By.xpath("//not-found"));
        actions.moveToElement(object20, 0, object20.getSize().getHeight() / 2)
                .clickAndHold()
                .moveToElement(relatedObject2, 0, -relatedObject2.getSize().getHeight() / 2)
                .release()
                .perform();

        driver.findElement(By.xpath("//body/div[7]/div[1]/input[1]")).click();

        driver.findElement(By.xpath("/html/body/div[11]/table/tbody/tr[16]/td[2]")).click();

        driver.quit();
    }
}